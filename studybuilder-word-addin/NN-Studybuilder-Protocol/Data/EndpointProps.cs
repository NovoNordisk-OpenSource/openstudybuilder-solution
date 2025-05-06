namespace NN_Studybuilder_Protocol.Data
{
    public class EndpointProps
    {
        [Newtonsoft.Json.JsonProperty("name", Required = Newtonsoft.Json.Required.Default)]
        public string Name { get; set; }
    }
}
