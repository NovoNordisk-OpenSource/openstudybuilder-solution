
namespace NN_Studybuilder_Protocol.Data
{
    /// <summary>
    /// Represents an environment in the StudyBuilder api, e.g. Test
    /// </summary>
    public class StudyBuilderApiEnvironment
    {
        public string Url { get; set; }
        public string ClientId { get; set; }
        public string TenantId { get; set; }
        public string Scopes { get; set; }
        public string DisplayName { get; set; }
        public bool Active { get; set; }
    }
}
