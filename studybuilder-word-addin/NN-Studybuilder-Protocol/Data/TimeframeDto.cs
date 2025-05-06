using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data
{
    [Newtonsoft.Json.JsonObject("timeframe")]
    public class TimeframeDto
    {
        [Newtonsoft.Json.JsonProperty("name", Required = Newtonsoft.Json.Required.Default)]
        public string Name { get; set; }
    }
}
