using Newtonsoft.Json;
using System.Collections.Generic;

namespace BreacherFrontend
{
    public class BreachResponse : ResponseBase
    {
        [JsonProperty("solution_image")]
        public string SolutionImage { get; set; }

        [JsonProperty("score")]
        public double Score { get; set; }

        [JsonProperty("sequence")]
        public List<int[]> Sequence { get; set; }

        [JsonProperty("sequence_text")]
        public List<string> SequenceText { get; set; }
    }
}
