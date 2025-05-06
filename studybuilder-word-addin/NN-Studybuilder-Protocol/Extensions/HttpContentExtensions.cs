using Newtonsoft.Json;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Extensions
{
    public static class HttpContentExtensions
    {
        public static async Task<T> Deserialize<T>(this HttpContent content)
        {
            using (var stream = await content.ReadAsStreamAsync())
            {
                using (var sr = new StreamReader(stream))
                using (var jsonTextReader = new JsonTextReader(sr))
                {
                    var serializer = new JsonSerializer();
                    return serializer.Deserialize<T>(jsonTextReader);
                }
            }
        }
    }
}
