using Newtonsoft.Json;

namespace BreacherFrontend
{
    public class ResponseBase
    {
        [JsonProperty("elapsed")]
        public double Elapsed { get; set; }

        [JsonProperty("errors")]
        public string Errors { get; set; }
    }
}
