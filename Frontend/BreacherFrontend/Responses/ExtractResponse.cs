using Newtonsoft.Json;
using System.Collections.Generic;

namespace BreacherFrontend
{
    public class ExtractResponse: ResponseBase
    {
        [JsonProperty("buffer_size")]
        public int BufferSize { get; set; }

        [JsonProperty("grid")]
        public List<List<string>> Grid { get; set; }

        [JsonProperty("matrix_image")]
        public string MatrixImage { get; set; }

        [JsonProperty("targets")]
        public List<List<string>> Targets { get; set; }

        [JsonProperty("grid_boxes")]
        public List<List<int[]>> GridBoxes { get; set; }
    }
}
