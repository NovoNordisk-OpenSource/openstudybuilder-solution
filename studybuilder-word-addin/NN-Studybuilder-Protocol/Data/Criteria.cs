using Newtonsoft.Json;

namespace NN_Studybuilder_Protocol.Data
{
    public class Criteria
    {
        [JsonProperty("uid")]
        public string Uid { get; set; }
        [JsonProperty("name")]
        public string Name { get; set; }
    }
}
