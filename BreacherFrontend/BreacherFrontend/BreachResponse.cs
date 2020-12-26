using Newtonsoft.Json;
using System.Collections.Generic;

namespace BreacherFrontend
{
    public class BreachResponse
    {
        [JsonProperty("buffer_size")]
        public int BufferSize { get; set; }

        [JsonProperty("elapsed")]
        public double Elapsed { get; set; }

        [JsonProperty("grid")]
        public List<List<string>> Grid { get; set; }

        [JsonProperty("result_image")]
        public string ResultImage { get; set; }

        [JsonProperty("score")]
        public double Score { get; set; }

        [JsonProperty("sequence")]
        public List<List<int>> Sequence { get; set; }

        [JsonProperty("sequence_text")]
        public List<string> SequenceText { get; set; }

        [JsonProperty("targets")]
        public List<List<string>> Targets { get; set; }
        
    }
}
