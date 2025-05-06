namespace NN_Studybuilder_Protocol.Data
{
    //[Newtonsoft.Json.JsonObject("endpointUnit")]
    public class EndpointUnitDto
    {
        [Newtonsoft.Json.JsonProperty("separator", Required = Newtonsoft.Json.Required.Default)]
        public string Separator { get; set; }

        [Newtonsoft.Json.JsonProperty("units", Required = Newtonsoft.Json.Required.Default)]
        public string[] Units { get; set; }
    }
}
