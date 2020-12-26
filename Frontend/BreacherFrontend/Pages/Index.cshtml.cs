using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace BreacherFrontend.Pages
{
    public class IndexModel : PageModel
    {
        private readonly ILogger<IndexModel> _logger;
        private readonly IHttpClientFactory _clientFactory;
        private readonly BreachCache _cache;
        private readonly IConfiguration _config;

        public IFormFile FormFile { get; set; }
        public BreachResponse BreachData { get; set; }

        public string Sequence { get; set; }
        public string Targets { get; set; }

        public IndexModel(ILogger<IndexModel> logger, IHttpClientFactory clientFactory, BreachCache cache, IConfiguration config)
        {
            _logger = logger;
            _clientFactory = clientFactory;
            _cache = cache;
            _config = config;
        }

        public void OnGet(string cacheKey)
        {
            _logger.LogInformation("OnGet Invoked {CacheKey}", cacheKey);
            if (!string.IsNullOrEmpty(cacheKey))
            {
                BreachResponse breachData = _cache.GetBreachResponse(cacheKey, true);
                if (breachData != null && breachData.SequenceText != null)
                {
                    BreachData = breachData;
                    Sequence = string.Join(" ", breachData.SequenceText);
                    Targets = "";
                    foreach (var seq in breachData.Targets)
                    {
                        Targets += string.Join(" ", seq) + "<br />";
                    }
                    _logger.LogInformation(Sequence);
                }
            }
        }

        public async Task<IActionResult> OnPostUploadAsync()
        {
            string key = null;
            if (FormFile?.Length > 0)
            {
                string url = _config["BackendURL"] + "/breach";
                HttpClient client = _clientFactory.CreateClient();
                using MemoryStream stream = new MemoryStream();
                await FormFile.CopyToAsync(stream);
                stream.Seek(0, SeekOrigin.Begin);
                
                MultipartFormDataContent formData = new MultipartFormDataContent();
                formData.Add(new StreamContent(stream), "file", FormFile.FileName);

                HttpResponseMessage response = await client.PostAsync(url, formData);
                response.EnsureSuccessStatusCode();

                string content = await response.Content.ReadAsStringAsync();
                BreachResponse breachData = JsonConvert.DeserializeObject<BreachResponse>(content);
                key = _cache.StoreBreachResponse(breachData);
            }

            return RedirectToPage("Index", new { cacheKey=key });
        }
    }
}
