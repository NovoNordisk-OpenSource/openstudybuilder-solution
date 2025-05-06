using NN_Studybuilder_Protocol.Data.Repositories;
using NN_Studybuilder_Protocol.StudybuildApi;
using RestSharp;
using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data.Services
{
    public class StudybuilderApiFactory
    {
        private readonly ConfigManager configManager;
        private readonly HttpClientHandler httpClientHandler;
        private readonly AuthenticationRepository authenticationRepository;

        public StudybuilderApiFactory(ConfigManager configManager, HttpClientHandler httpClientHandler, AuthenticationRepository authenticationRepository)
        {
            this.configManager = configManager;
            this.httpClientHandler = httpClientHandler;
            this.authenticationRepository = authenticationRepository;
        }

        /// <summary>
        /// Get the Studybuilder api client generated from swagger
        /// </summary>
        /// <returns></returns>
        public async Task<StudyBuilderClient> Build()
        {
            var httpClient = new HttpClient(httpClientHandler)
            {
                BaseAddress = new Uri(configManager.StudyBuilder_ApiUrl)
            };

            var accessToken = await authenticationRepository.GetAccessTokenForStudyBuilder();
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

            return new StudyBuilderClient(httpClient) { ReadResponseAsString = true };
        }

        /// <summary>
        /// Get the Http client for the Studybuilder api
        /// </summary>
        /// <returns></returns>
        public async Task<HttpClient> GetStudybuilderHttpClient()
        {
            var uriBuilder = new System.Text.StringBuilder();
            uriBuilder.Append(configManager.StudyBuilder_ApiUrl.TrimEnd('/'));
            uriBuilder.Append('/'); // Ensure only one slash

            var httpClient = new HttpClient(httpClientHandler)
            {
                BaseAddress = new Uri(uriBuilder.ToString())
            };

            var accessToken = await authenticationRepository.GetAccessTokenForStudyBuilder();
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

            httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
            httpClient.DefaultRequestHeaders.Add("x-test-user-id", "NN-StudyBuilder Word add-in");

            return httpClient;
        }

        public async Task<RestClient> GetRestClient()
        {
            var client = new RestClient(configManager.StudyBuilder_ApiUrl);

            var token = await authenticationRepository.GetAccessTokenForStudyBuilder();
            client.AddDefaultHeader("Authorization", $"Bearer {token}");

            return client;
        }
    }
}
