using Newtonsoft.Json;
using NN_Studybuilder_Protocol.Data.Services;
using NN_Studybuilder_Protocol.Exceptions;
using NN_Studybuilder_Protocol.StudybuildApi;
using RestSharp;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data.Repositories
{
    public class StudyRepository
    {
        private readonly StudybuilderApiFactory studybuilderApiFactory;
        readonly string x_test_user_id = "word add-in";

        public StudyRepository(StudybuilderApiFactory studybuilderApiFactory)
        {
            this.studybuilderApiFactory = studybuilderApiFactory;
        }

        protected void AddDefaultHeaders(HttpClient httpClient, string accessToken)
        {
            httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
            httpClient.DefaultRequestHeaders.Add("x-test-user-id", x_test_user_id);
        }

        public async Task<IEnumerable<StudyDto>> GetAll()
        {
            // Generated client no longer works
            //var apiClient = studybuilderApiFactory.Build();
            //apiClient.ReadResponseAsString = true;
            //var studies = apiClient.StudiesGetAsyncCustom("+uid,+projectNumber,+studyId, +currentMetadata.identificationMetadata, -currentMetadata.studyPopulation, -currentMetadata.highLevelStudyDesign").Result;
            //var studies = apiClient.StudiesGetAsync("+uid,+projectNumber,+studyId, +currentMetadata.identificationMetadata, -currentMetadata.studyPopulation, -currentMetadata.highLevelStudyDesign",
            //   false, false, false, false, false, "{\"uid\": true}", null, null, null, null, true, "word add-in").Result;

            var client = await studybuilderApiFactory.GetRestClient();

            //var response = client.GetAsync<CustomPage_Study>(new RestRequest("studies")).ConfigureAwait(false);
            var response = await client.ExecuteGetAsync(new RestRequest("studies?page_size=0"));

            if (!response.IsSuccessful)
            {
                if (response.StatusCode == System.Net.HttpStatusCode.BadGateway)
                {
                    // StudyBuilder api is not available: we must show this in the ui
                    throw new StudyBuilderNotAvailableException();
                }

                throw new Exception("", response.ErrorException ?? new Exception(response.ErrorMessage));
            }

            var r = JsonConvert.DeserializeObject<CustomPage_CompactStudy_>(response.Content);
            var result = new List<StudyDto>();
            foreach (var study in r.Items)
            {
                var mapped = MapFrom(study);
                result.Add(mapped);
            }

            return result;
        }

        public async Task<IEnumerable<StudyDto>> Search(string term)
        {
            var client = await studybuilderApiFactory.GetRestClient();

            var filters = "{\"current_metadata.identification_metadata.study_id\":{\"v\":[\"" + term + "\"], \"op\":\"co\"}, \"current_metadata.identification_metadata.study_acronym\":{\"v\":[\"" + term + "\"], \"op\":\"co\"}}";
            var response = await client.ExecuteGetAsync(new RestRequest($"studies?page_size=0&filters={filters}&operator=or"));

            if (!response.IsSuccessful)
            {
                if (response.StatusCode == System.Net.HttpStatusCode.BadGateway)
                {
                    // StudyBuilder api is not available: we must show this in the ui
                    throw new StudyBuilderNotAvailableException();
                }

                throw new Exception("", response.ErrorException ?? new Exception(response.ErrorMessage));
            }

            var r = JsonConvert.DeserializeObject<CustomPage_CompactStudy_>(response.Content);
            var result = new List<StudyDto>();
            foreach (var study in r.Items)
            {
                var mapped = MapFrom(study);
                result.Add(mapped);
            }

            return result;
        }
        protected virtual StudyDto MapFrom(CompactStudy study)
        {
            var dto = new StudyDto();
            dto.Uid = study.Uid;
            if (study.Current_metadata != null && study.Current_metadata.Identification_metadata != null)
            {
                dto.ProjectNumber = study.Current_metadata.Identification_metadata.Project_number;
                dto.StudyAcronym = study.Current_metadata.Identification_metadata.Study_acronym;
                dto.StudyNumber = study.Current_metadata.Identification_metadata.Study_number;
                dto.StudyId = study.Current_metadata.Identification_metadata.Study_id;
            }
            if (study.Current_metadata.Version_metadata != null)
            {
                dto.Status = study.Current_metadata.Version_metadata.Study_status;
                dto.VersionTimestamp = study.Current_metadata.Version_metadata.Version_timestamp.ToString("yyyy-MM-dd");
                dto.VersionNumber = study.Current_metadata.Version_metadata.Version_number.ToString();
            }

            return dto;
        }

        public async Task<Clinical_mdr_api__models__study_selections__study__Study> GetStudyById(string uid, string version = null)
        {
            var apiClient = await studybuilderApiFactory.Build();
            var v = new List<StudyComponentEnum>() { StudyComponentEnum.Identification_metadata, StudyComponentEnum.Registry_identifiers, StudyComponentEnum.Version_metadata };
            var study = await apiClient.StudiesGetAsync(uid, v, null, null, version, CancellationToken.None);
            //    uid,
            //    "+uid,+projectNumber,+studyId, +currentMetadata.identificationMetadata, -currentMetadata.studyPopulation, -currentMetadata.highLevelStudyDesign").Result;
            //var result = MapFrom(study);

            return study;
        }

        public async Task<IEnumerable<StudySelectionObjective>> GetStudySelectionObjective(string studyUid)
        {
            return await Get<ICollection<StudySelectionObjective>>($"studies/{studyUid}/study-objectives");

            //// Currently not issuing Http.StatusCode 400 Not found ,so the generated client fails
            //Client apiClient = studybuilderApiFactory.Build();
            //return apiClient.StudyStudyObjectivesGetAsync(studyUid).Result;
        }

        public async Task<IEnumerable<EndpointDto>> GetStudyEndpoints(string studyUid)
        {
            // Use custom odata object + client here as the data structure was not supported in swagger at the time of implementing
            var httpClient = await studybuilderApiFactory.GetStudybuilderHttpClient();
            var response = await httpClient.GetAsync($"studies/{studyUid}/study-endpoints");
            using (var stream = response.Content.ReadAsStreamAsync().Result)
            using (var jr = new JsonTextReader(new StreamReader(stream)))
            {
                JsonSerializer js = new JsonSerializer();
                return js.Deserialize<EndpointDto[]>(jr);
            }
        }

        public async Task<ProtocolTitleDto> GetProtocolTitle(string studyUid, string version = null)
        {
            var query = $"studies/{studyUid}/protocol-title";
            var httpClient = await studybuilderApiFactory.GetStudybuilderHttpClient();
            if (!string.IsNullOrWhiteSpace(version))
                query += $"?study_value_version={version}";

            var response = await httpClient.GetAsync(query);
            using (var stream = await response.Content.ReadAsStreamAsync())
            using (var jr = new JsonTextReader(new StreamReader(stream)))
            {
                JsonSerializer js = new JsonSerializer();
                return js.Deserialize<ProtocolTitleDto>(jr);
            }
        }
              

        protected async Task<T> Get<T>(string request) where T : class
        {
            // Use custom odata object + client here as the data structure was not supported in swagger at the time of implementing
            var httpClient = await studybuilderApiFactory.GetStudybuilderHttpClient();
            var request_ = new HttpRequestMessage
            {
                Method = new HttpMethod("GET"),
                RequestUri = new Uri(request, UriKind.RelativeOrAbsolute)
            };

            var response = await httpClient.SendAsync(request_);
            response.EnsureSuccessStatusCode();

            using (var stream = await response.Content.ReadAsStreamAsync())
            using (var jr = new JsonTextReader(new StreamReader(stream)))
            {
                JsonSerializer js = new JsonSerializer();
                return js.Deserialize<T>(jr);
            }
        }

        public async Task<byte[]> GetFlowchart(string studyUid)
        {
            // Had to use RestSharp as HttpClient and WebClient could not read content-length header and thus cut-off the response content making the downloaded docx file unreadable for Word when inserting the file
            var resource = $"studies/{studyUid}/flowchart.docx";
            var client = await studybuilderApiFactory.GetRestClient();
            var request = new RestRequest(resource, Method.Get);
            return await client.DownloadDataAsync(request);
        }

        public async Task<IEnumerable<StudySelectionCriteria>> GetInclusionCriteria(string studyUid, string version = null)
        {
            var apiClient = await studybuilderApiFactory.Build();
            //return apiClient.StudyStudyCriteriaGetAsyncCustom(studyUid, true, "{\"criteria_type.sponsor_preferred_name_sentence_case\":{\"v\":[\"inclusion criteria\"]}}", null, x_test_user_id).Result;
            var res = await apiClient.StudiesStudyCriteriaGetAsync(studyUid, no_brackets: true, sort_by: null, page_number: 1, page_size: 0, filters: "{\"criteria_type.sponsor_preferred_name_sentence_case\":{\"v\":[\"inclusion criteria\"]}}", @operator: "and", total_count: false, study_value_version: version);
            return res.Items;
        }

        public async Task<IEnumerable<StudySelectionCriteria>> GetExclusionCriteria(string studyUid, string version = null)
        {
            var apiClient = await studybuilderApiFactory.Build();
            //var custom = apiClient.StudyStudyCriteriaGetAsyncCustom(studyUid, true, "{\"criteria_type.sponsor_preferred_name_sentence_case\":{\"v\":[\"exclusion criteria\"]}}", null, x_test_user_id).Result;
            var res = await apiClient.StudiesStudyCriteriaGetAsync(studyUid, no_brackets: true, sort_by: null, page_number: null, page_size: 0, filters: "{\"criteria_type.sponsor_preferred_name_sentence_case\":{\"v\":[\"exclusion criteria\"]}}", @operator: null, total_count: null, study_value_version: version);
            return res.Items;
        }

        public async Task<byte[]> GetObjectivesEndpoints(string studyUid, string version = null)
        {
            var query = $"studies/{studyUid}/study-objectives.docx";
            if (!string.IsNullOrWhiteSpace(version))
            {
                query += $"?study_value_version={version}";
            }

            // Had to use RestSharp as HttpClient and WebClient could not read content-length header and thus cut-off the response content making the downloaded docx file unreadable for Word when inserting the file
            var client = await studybuilderApiFactory.GetRestClient();
            var request = new RestRequest(query, Method.Get);
            return await client.DownloadDataAsync(request);
        }

        public async Task<IEnumerable<StudyDto>> GetStudyVersions(string studyUid)
        {
            var client = await studybuilderApiFactory.GetRestClient();
            var response = await client.ExecuteGetAsync(new RestRequest($"studies/{studyUid}/snapshot-history"));

            if (!response.IsSuccessful)
            {
                if (response.StatusCode == System.Net.HttpStatusCode.BadGateway)
                {
                    // StudyBuilder api is not available: we must show this in the ui
                    throw new StudyBuilderNotAvailableException();
                }

                throw new Exception("", response.ErrorException ?? new Exception(response.ErrorMessage));
            }

            var r = JsonConvert.DeserializeObject<CustomPage_CompactStudy_>(response.Content);
            var result = new List<StudyDto>();
            foreach (var study in r.Items)
            {
                var mapped = MapFrom(study);
                result.Add(mapped);
            }

            return result;
        }

        public async Task<byte[]> GetStudyDesign(string studyUid, string version = null)
        {
            var query = $"studies/{studyUid}/design.svg";
            if (!string.IsNullOrWhiteSpace(version))
            {
                query += $"?study_value_version={version}";
            }

            // Had to use RestSharp as HttpClient and WebClient could not read content-length header and thus cut-off the response content making the downloaded docx file unreadable for Word when inserting the file
            var client = await studybuilderApiFactory.GetRestClient();
            var request = new RestRequest(query, Method.Get);
            return await client.DownloadDataAsync(request);
        }
    }
}