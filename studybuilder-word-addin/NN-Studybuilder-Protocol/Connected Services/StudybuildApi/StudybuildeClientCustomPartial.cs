using NN_Studybuilder_Protocol.Data.StudybuilderApi;
using NN_Studybuilder_Protocol.Data;

namespace NN_Studybuilder_Protocol.StudybuildApi
{
    public partial class StudyBuilderClient
    {
        /// <summary>
        /// Customized version of StudiesGetAsync as the generated version does not follow the swagger schema properly
        /// </summary>
        /// <param name="fields">Select or exclude fields returned in the response</param>
        /// <returns>Custom class StudiesDto</returns>
        public System.Threading.Tasks.Task<StudiesDto> StudiesGetAsyncCustom(string fields)
        {
            return StudiesGetAsyncCustom(fields, System.Threading.CancellationToken.None);
        }

        /// <summary>
        /// Customized version of StudiesGetAsync as the generated version does not follow the swagger schema properly
        /// </summary>
        public async System.Threading.Tasks.Task<StudiesDto> StudiesGetAsyncCustom(string fields, System.Threading.CancellationToken cancellationToken)
        {
            var urlBuilder_ = new System.Text.StringBuilder();
            urlBuilder_.Append(BaseUrl != null ? BaseUrl.TrimEnd('/') : "").Append("/studies?");
            if (fields != null)
            {
                urlBuilder_.Append(System.Uri.EscapeDataString("fields") + "=").Append(System.Uri.EscapeDataString(ConvertToString(fields, System.Globalization.CultureInfo.InvariantCulture))).Append("&");
            }
            urlBuilder_.Length--;

            var client_ = _httpClient;
            var disposeClient_ = false;
            try
            {
                using (var request_ = new System.Net.Http.HttpRequestMessage())
                {
                    request_.Method = new System.Net.Http.HttpMethod("GET");
                    request_.Headers.Accept.Add(System.Net.Http.Headers.MediaTypeWithQualityHeaderValue.Parse("application/json"));

                    PrepareRequest(client_, request_, urlBuilder_);

                    var url_ = urlBuilder_.ToString();
                    request_.RequestUri = new System.Uri(url_, System.UriKind.RelativeOrAbsolute);

                    PrepareRequest(client_, request_, url_);

                    var response_ = await client_.SendAsync(request_, System.Net.Http.HttpCompletionOption.ResponseHeadersRead, cancellationToken).ConfigureAwait(false);
                    var disposeResponse_ = true;
                    try
                    {
                        var headers_ = System.Linq.Enumerable.ToDictionary(response_.Headers, h_ => h_.Key, h_ => h_.Value);
                        if (response_.Content != null && response_.Content.Headers != null)
                        {
                            foreach (var item_ in response_.Content.Headers)
                                headers_[item_.Key] = item_.Value;
                        }

                        ProcessResponse(client_, response_);

                        var status_ = (int)response_.StatusCode;
                        if (status_ == 200)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<StudiesDto>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            return objectResponse_.Object;
                        }
                        else
                        if (status_ == 500)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<ErrorResponse>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<ErrorResponse>("Internal Server Error", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        if (status_ == 422)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<HTTPValidationError>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<HTTPValidationError>("Validation Error", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        {
                            var responseData_ = response_.Content == null ? null : await response_.Content.ReadAsStringAsync().ConfigureAwait(false);
                            throw new ApiException("The HTTP status code of the response was not expected (" + status_ + ").", status_, responseData_, headers_, null);
                        }
                    }
                    finally
                    {
                        if (disposeResponse_)
                            response_.Dispose();
                    }
                }
            }
            finally
            {
                if (disposeClient_)
                    client_.Dispose();
            }
        }

        public System.Threading.Tasks.Task<StudySelectionCriteriaDto> StudyStudyCriteriaGetAsyncCustom(string uid, bool? noBrackets, string filters, string @operator, string x_test_user_id)
        {
            return StudyStudyCriteriaGetAsyncCustom(uid, noBrackets, filters, @operator, x_test_user_id, System.Threading.CancellationToken.None);
        }

        /// <param name="cancellationToken">A cancellation token that can be used by other objects or threads to receive notice of cancellation.</param>
        /// <summary>Returns all study criteria currently selected for study with provided uid</summary>
        /// <param name="uid">The unique id of the study.</param>
        /// <param name="noBrackets">Indicates whether brackets around Template Parameters in the Criteriashould be returned</param>
        /// <param name="filters">Optionally, a dictionary of fieldNames and searchStrings with a choice of operators.
        /// <br/>
        /// <br/>Default: {} (no filtering)
        /// <br/>
        /// <br/>Functionality: filters the return values based on the provided search strings and operators.
        /// <br/>
        /// <br/>The expected format is the following : {"labelName":{"v":[list of values to filter against], "op":"comparison operator"}, "otherLabelName":{...}}
        /// <br/>
        /// <br/>If a list of values is provided for a given labelName, it will execute an OR on these values.
        /// <br/>
        /// <br/>Supported comparison operators are the following : eq (default, =), ne (not equals), co (string contains), ge (greater or equal to), gt (greater than), le (less or equal to), lt (less than), bw (between - exactly two values are required).
        /// <br/>
        /// <br/>Note that this is not just for string filtering. For example, this works as filter : {"isGlobalStandard": {"v": [false]}}
        /// <br/>
        /// <br/>Wildcard filtering is also supported. To do this, provide * as labelName, with the same structure for values and operator : {"*":{"v":["searchString"]}}
        /// <br/>
        /// <br/>Wildcard only supports searching strings, on labels of type string ; with a contains operator (set as default in this case).
        /// <br/>
        /// <br/>Finally, you can filter on items that have an empty value for a field. To achieve this, just set the "v" list to the empty array [].</param>
        /// <param name="operator">Optionally, if the filter must be done on several fields, the and/or operator to use.
        /// <br/>
        /// <br/>Default: and (all field names have to match their filter).
        /// <br/>
        /// <br/>Functionality: and/or apply to all fields. 'and' will require filters to match, 'or' will require any filters to match.</param>
        /// <param name="x_test_user_id">A value to be injected into service as user id.</param>
        /// <returns>Successful Response</returns>
        /// <exception cref="ApiException">A server side error occurred.</exception>
        public async System.Threading.Tasks.Task<StudySelectionCriteriaDto> StudyStudyCriteriaGetAsyncCustom(string uid, bool? noBrackets, string filters, string @operator, string x_test_user_id, System.Threading.CancellationToken cancellationToken)
        {
            if (uid == null)
                throw new System.ArgumentNullException("uid");

            var urlBuilder_ = new System.Text.StringBuilder();
            urlBuilder_.Append(BaseUrl != null ? BaseUrl.TrimEnd('/') : "").Append("/studies/{uid}/study-criteria?");
            urlBuilder_.Replace("{uid}", System.Uri.EscapeDataString(ConvertToString(uid, System.Globalization.CultureInfo.InvariantCulture)));
            if (noBrackets != null)
            {
                urlBuilder_.Append(System.Uri.EscapeDataString("no_brackets") + "=").Append(System.Uri.EscapeDataString(ConvertToString(noBrackets, System.Globalization.CultureInfo.InvariantCulture))).Append("&");
            }
            if (filters != null)
            {
                urlBuilder_.Append(System.Uri.EscapeDataString("filters") + "=").Append(System.Uri.EscapeDataString(ConvertToString(filters, System.Globalization.CultureInfo.InvariantCulture))).Append("&");
            }
            if (@operator != null)
            {
                urlBuilder_.Append(System.Uri.EscapeDataString("operator") + "=").Append(System.Uri.EscapeDataString(ConvertToString(@operator, System.Globalization.CultureInfo.InvariantCulture))).Append("&");
            }
            urlBuilder_.Length--;

            var client_ = _httpClient;
            var disposeClient_ = false;
            try
            {
                using (var request_ = new System.Net.Http.HttpRequestMessage())
                {
                    if (x_test_user_id != null)
                        request_.Headers.TryAddWithoutValidation("x-test-user-id", ConvertToString(x_test_user_id, System.Globalization.CultureInfo.InvariantCulture));
                    request_.Method = new System.Net.Http.HttpMethod("GET");
                    request_.Headers.Accept.Add(System.Net.Http.Headers.MediaTypeWithQualityHeaderValue.Parse("application/json"));

                    PrepareRequest(client_, request_, urlBuilder_);

                    var url_ = urlBuilder_.ToString();
                    request_.RequestUri = new System.Uri(url_, System.UriKind.RelativeOrAbsolute);

                    PrepareRequest(client_, request_, url_);

                    var response_ = await client_.SendAsync(request_, System.Net.Http.HttpCompletionOption.ResponseHeadersRead, cancellationToken).ConfigureAwait(false);
                    var disposeResponse_ = true;
                    try
                    {
                        var headers_ = System.Linq.Enumerable.ToDictionary(response_.Headers, h_ => h_.Key, h_ => h_.Value);
                        if (response_.Content != null && response_.Content.Headers != null)
                        {
                            foreach (var item_ in response_.Content.Headers)
                                headers_[item_.Key] = item_.Value;
                        }

                        ProcessResponse(client_, response_);

                        var status_ = (int)response_.StatusCode;
                        if (status_ == 200)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<StudySelectionCriteriaDto>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            return objectResponse_.Object;
                        }
                        else
                        if (status_ == 500)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<ErrorResponse>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<ErrorResponse>("Internal Server Error", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        if (status_ == 422)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<HTTPValidationError>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<HTTPValidationError>("Validation Error", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        {
                            var responseData_ = response_.Content == null ? null : await response_.Content.ReadAsStringAsync().ConfigureAwait(false);
                            throw new ApiException("The HTTP status code of the response was not expected (" + status_ + ").", status_, responseData_, headers_, null);
                        }
                    }
                    finally
                    {
                        if (disposeResponse_)
                            response_.Dispose();
                    }
                }
            }
            finally
            {
                if (disposeClient_)
                    client_.Dispose();
            }
        }

        /// <summary>Retrieve all information related to Protocol Title</summary>
        /// <param name="uid">The unique id of the study.</param>
        /// <param name="x_test_user_id">A value to be injected into service as user id.</param>
        /// <returns>Successful Response</returns>
        /// <exception cref="ApiException">A server side error occurred.</exception>
        public System.Threading.Tasks.Task<ProtocolTitleDto> StudiesProtocolTitleDtoAsync(string uid, string x_test_user_id)
        {
            return StudiesProtocolTitleDtoAsync(uid, x_test_user_id, System.Threading.CancellationToken.None);
        }

        /// <param name="cancellationToken">A cancellation token that can be used by other objects or threads to receive notice of cancellation.</param>
        /// <summary>Retrieve all information related to Protocol Title</summary>
        /// <param name="uid">The unique id of the study.</param>
        /// <param name="x_test_user_id">A value to be injected into service as user id.</param>
        /// <returns>Successful Response</returns>
        /// <exception cref="ApiException">A server side error occurred.</exception>
        public async System.Threading.Tasks.Task<ProtocolTitleDto> StudiesProtocolTitleDtoAsync(string uid, string x_test_user_id, System.Threading.CancellationToken cancellationToken)
        {
            if (uid == null)
                throw new System.ArgumentNullException("uid");

            var urlBuilder_ = new System.Text.StringBuilder();
            urlBuilder_.Append(BaseUrl != null ? BaseUrl.TrimEnd('/') : "").Append("/studies/{uid}/protocol-title");
            urlBuilder_.Replace("{uid}", System.Uri.EscapeDataString(ConvertToString(uid, System.Globalization.CultureInfo.InvariantCulture)));

            var client_ = _httpClient;
            var disposeClient_ = false;
            try
            {
                using (var request_ = new System.Net.Http.HttpRequestMessage())
                {
                    if (x_test_user_id != null)
                        request_.Headers.TryAddWithoutValidation("x-test-user-id", ConvertToString(x_test_user_id, System.Globalization.CultureInfo.InvariantCulture));
                    request_.Method = new System.Net.Http.HttpMethod("GET");
                    request_.Headers.Accept.Add(System.Net.Http.Headers.MediaTypeWithQualityHeaderValue.Parse("application/json"));

                    PrepareRequest(client_, request_, urlBuilder_);

                    var url_ = urlBuilder_.ToString();
                    request_.RequestUri = new System.Uri(url_, System.UriKind.RelativeOrAbsolute);

                    PrepareRequest(client_, request_, url_);

                    var response_ = await client_.SendAsync(request_, System.Net.Http.HttpCompletionOption.ResponseHeadersRead, cancellationToken).ConfigureAwait(false);
                    var disposeResponse_ = true;
                    try
                    {
                        var headers_ = System.Linq.Enumerable.ToDictionary(response_.Headers, h_ => h_.Key, h_ => h_.Value);
                        if (response_.Content != null && response_.Content.Headers != null)
                        {
                            foreach (var item_ in response_.Content.Headers)
                                headers_[item_.Key] = item_.Value;
                        }

                        ProcessResponse(client_, response_);

                        var status_ = (int)response_.StatusCode;
                        if (status_ == 200)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<ProtocolTitleDto>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            return objectResponse_.Object;
                        }
                        else
                        if (status_ == 404)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<ErrorResponse>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<ErrorResponse>("Not Found - The study with the specified \'uid\' wasn\'t found.", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        if (status_ == 500)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<ErrorResponse>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<ErrorResponse>("Internal Server Error", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        if (status_ == 422)
                        {
                            var objectResponse_ = await ReadObjectResponseAsync<HTTPValidationError>(response_, headers_, cancellationToken).ConfigureAwait(false);
                            if (objectResponse_.Object == null)
                            {
                                throw new ApiException("Response was null which was not expected.", status_, objectResponse_.Text, headers_, null);
                            }
                            throw new ApiException<HTTPValidationError>("Validation Error", status_, objectResponse_.Text, headers_, objectResponse_.Object, null);
                        }
                        else
                        {
                            var responseData_ = response_.Content == null ? null : await response_.Content.ReadAsStringAsync().ConfigureAwait(false);
                            throw new ApiException("The HTTP status code of the response was not expected (" + status_ + ").", status_, responseData_, headers_, null);
                        }
                    }
                    finally
                    {
                        if (disposeResponse_)
                            response_.Dispose();
                    }
                }
            }
            finally
            {
                if (disposeClient_)
                    client_.Dispose();
            }
        }
    }
}