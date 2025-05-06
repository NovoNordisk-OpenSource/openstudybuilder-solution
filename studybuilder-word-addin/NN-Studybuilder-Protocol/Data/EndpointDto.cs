using System;

namespace NN_Studybuilder_Protocol.Data
{
    [Newtonsoft.Json.JsonObject("endpoint")]
    public class EndpointDto
    {
        [Newtonsoft.Json.JsonProperty("order", Required = Newtonsoft.Json.Required.Default)]
        public int Order { get; set; }

        [Newtonsoft.Json.JsonProperty("endpoint", Required = Newtonsoft.Json.Required.Default)]
        public EndpointProps Props{ get; set; }

        [Newtonsoft.Json.JsonProperty("studyUid", Required = Newtonsoft.Json.Required.Default)]
        public Guid StudyUid { get; set; }

        [Newtonsoft.Json.JsonProperty("endpointLevel", Required = Newtonsoft.Json.Required.Default)]
        public string EndpointLevel { get; set; }

        [Newtonsoft.Json.JsonProperty("endpointUnits", Required = Newtonsoft.Json.Required.Default)]
        public EndpointUnitDto EndpointUnits { get; set; }

        [Newtonsoft.Json.JsonProperty("timeframe", Required = Newtonsoft.Json.Required.Default)]
        public TimeframeDto Timeframe { get; set; }

        [Newtonsoft.Json.JsonProperty("studyObjective", Required = Newtonsoft.Json.Required.Default)]
        public StudyObjectiveDto StudyObjective { get; set; }
    }
}
