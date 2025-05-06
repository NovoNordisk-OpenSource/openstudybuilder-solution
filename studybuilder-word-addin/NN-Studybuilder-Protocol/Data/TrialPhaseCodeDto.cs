using Newtonsoft.Json;

namespace NN_Studybuilder_Protocol.Data
{
    public class TrialPhaseCodeDto
    {
        [JsonProperty("term_uid")]
        public string TermUid { get; set; }

        [JsonProperty("name")]
        public string Name { get; set; }
    }
}
