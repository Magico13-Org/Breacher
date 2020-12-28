using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace BreacherFrontend.Pages
{
    public class IndexModel : PageModel
    {
        private readonly ILogger<IndexModel> _logger;
        private readonly IHttpClientFactory _clientFactory;
        private readonly ResponseCache _cache;
        private readonly IConfiguration _config;

        public IFormFile FormFile { get; set; }
        public BreachResponse BreachData { get; set; }
        public ExtractResponse ExtractedFields { get; set; }

        public string Sequence { get; set; }
        public string SequencePositions { get; set; }


        [BindProperty]
        public string Targets { get; set; }
        [BindProperty]
        public string Grid { get; set; }
        [BindProperty]
        [Range(2, 20)]
        public int BufferSize { get; set; } = 4;
        [BindProperty, HiddenInput]
        public string ExtractedImage { get; set; }
        [BindProperty, HiddenInput]
        public string GridBoxes { get; set; }

        public int TargetCount { get; set; } = 3;
        public int GridSize { get; set; } = 6;

        public IndexModel(ILogger<IndexModel> logger, IHttpClientFactory clientFactory, ResponseCache cache, IConfiguration config)
        {
            _logger = logger;
            _clientFactory = clientFactory;
            _cache = cache;
            _config = config;
        }

        public void OnGet(string dataKey, string breachKey)
        {
            _logger.LogInformation("OnGet Invoked {DataKey} {BreachKey}", dataKey, breachKey);
            if (!string.IsNullOrEmpty(dataKey))
            {
                ExtractResponse extractData = _cache.GetResponse<ExtractResponse>(dataKey, true);
                if (extractData != null && extractData.Targets != null)
                {
                    ExtractedFields = extractData;
                    BufferSize = extractData.BufferSize;
                    StringBuilder tgtsBuilder = new StringBuilder();
                    foreach (List<string> seq in extractData.Targets)
                    {
                        tgtsBuilder.AppendLine(string.Join(" ", seq));
                    }
                    Targets = tgtsBuilder.ToString().TrimEnd();

                    StringBuilder gridBuilder = new StringBuilder();
                    foreach (List<string> seq in extractData.Grid)
                    {
                        gridBuilder.AppendLine(string.Join(" ", seq));
                    }
                    Grid = gridBuilder.ToString().TrimEnd();

                    TargetCount = extractData.Targets.Count;
                    GridSize = extractData.Grid.Count;

                    ExtractedImage = extractData.MatrixImage;
                    GridBoxes = JsonConvert.SerializeObject(extractData.GridBoxes);
                }
            }
            if (!string.IsNullOrEmpty(breachKey))
            {
                BreachResponse breachData = _cache.GetResponse<BreachResponse>(breachKey, true);
                if (breachData != null && breachData.Sequence != null)
                {
                    BreachData = breachData;
                    Sequence = string.Join(" ", breachData.SequenceText);
                    SequencePositions = "";
                    foreach (int[] pos in breachData.Sequence)
                    {
                        SequencePositions += $"({pos[0]+1}, {pos[1]+1}) ";
                    }
                    SequencePositions = SequencePositions.TrimEnd();
                }
            }
        }

        public async Task<IActionResult> OnPostSolveAsync()
        {
            string dataKey = null;
            ExtractResponse data = null;
            HttpClient client = _clientFactory.CreateClient();
            if (FormFile?.Length > 0)
            {
                dataKey = await ExtractDataAsync(client, FormFile);
                data = _cache.GetResponse<ExtractResponse>(dataKey);
            }
            else
            {
                if (BufferSize > 0 && !string.IsNullOrEmpty(Targets) && !string.IsNullOrEmpty(Grid))
                {
                    List<List<string>> targets = new List<List<string>>();
                    List<List<string>> grid = new List<List<string>>();

                    foreach (string line in Targets.Split(new char[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        targets.Add(line.Split().ToList());
                    }

                    foreach (string line in Grid.Split(new char[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        grid.Add(line.Split().ToList());
                    }

                    data = new ExtractResponse()
                    {
                        BufferSize = BufferSize,
                        Grid = grid,
                        GridBoxes = JsonConvert.DeserializeObject<List<List<int[]>>>(GridBoxes),
                        MatrixImage = ExtractedImage,
                        Targets = targets
                    };

                    dataKey = _cache.StoreResponse(data);
                }
            }
            string breachKey = await BreachAsync(client, data);

            return RedirectToPage("Index", new { dataKey, breachKey });
        }


        internal async Task<string> ExtractDataAsync(HttpClient client, IFormFile file)
        {
            string extractUrl = _config["BackendURL"] + "/extract";
            using MemoryStream stream = new MemoryStream();
            await file.CopyToAsync(stream);
            stream.Seek(0, SeekOrigin.Begin);

            MultipartFormDataContent formData = new MultipartFormDataContent();
            formData.Add(new StreamContent(stream), "file", file.FileName);

            HttpResponseMessage response = await client.PostAsync(extractUrl, formData);
            response.EnsureSuccessStatusCode();

            string content = await response.Content.ReadAsStringAsync();
            ExtractResponse extractData = JsonConvert.DeserializeObject<ExtractResponse>(content);
            return _cache.StoreResponse(extractData);
        }

        internal async Task<string> BreachAsync(HttpClient client, ExtractResponse extractData)
        {
            string breachUrl = _config["BackendURL"] + "/breach";

            string requestContent = JsonConvert.SerializeObject(extractData);

            HttpResponseMessage response = await client.PostAsync(breachUrl, new StringContent(requestContent, Encoding.UTF8, "application/json"));
            response.EnsureSuccessStatusCode();

            string content = await response.Content.ReadAsStringAsync();
            BreachResponse breachData = JsonConvert.DeserializeObject<BreachResponse>(content);
            return _cache.StoreResponse(breachData);
        }
    }
}
