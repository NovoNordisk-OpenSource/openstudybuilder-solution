using Microsoft.Identity.Client;
using NN_Studybuilder_Protocol.Data.Services;
using System.Linq;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data.Repositories
{
    public class AuthenticationRepository
    {
        private readonly ConfigManager configManager;
        private readonly PublicClientAppFactory publicClientAppFactory;
        private IPublicClientApplication publicClientApp;

        public AuthenticationRepository(ConfigManager configManager, PublicClientAppFactory publicClientAppFactory)
        {
            this.configManager = configManager;
            this.publicClientAppFactory = publicClientAppFactory;
        }

        string[] scopes;
        string[] Scopes
        {
            get
            {
                if (scopes == null)
                {
                    scopes = configManager.StudyBuilder_Scopes.Split(new string[] { "," }, System.StringSplitOptions.RemoveEmptyEntries);
                }

                return scopes;
            }
        }

        //public async Task<string> GetAccessTokenForStudyBuilder()
        //{
        //    AuthenticationResult result = null;
        //    publicClientApp = await publicClientAppFactory.Create();
        //    var accounts = await publicClientApp.GetAccountsAsync();
        //    if (accounts.Any())
        //    {
        //        result = await publicClientApp.AcquireTokenSilent(Scopes, accounts.FirstOrDefault()).ExecuteAsync();
        //    }
        //    else
        //    {
        //        try
        //        {
        //            result = await publicClientApp.AcquireTokenInteractive(Scopes).ExecuteAsync();
        //            //result = await publicClientApp.AcquireTokenByIntegratedWindowsAuth(scopes).ExecuteAsync(CancellationToken.None); // Requires device enrollment for MFA
        //        }
        //        catch (MsalUiRequiredException ex)
        //        {
        //            result = await publicClientApp.AcquireTokenInteractive(Scopes).ExecuteAsync();
        //            // MsalUiRequiredException: AADSTS65001: The user or administrator has not consented to use the application
        //            // with ID '{appId}' named '{appName}'.Send an interactive authorization request for this user and resource.

        //            // you need to get user consent first. This can be done, if you are not using .NET Core (which does not have any Web UI)
        //            // by doing (once only) an AcquireToken interactive.

        //            // If you are using .NET core or don't want to do an AcquireTokenInteractive, you might want to suggest the user to navigate
        //            // to a URL to consent: https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={clientId}&response_type=code&scope=user.read

        //            // AADSTS50079: The user is required to use multi-factor authentication.
        //            // There is no mitigation - if MFA is configured for your tenant and AAD decides to enforce it,
        //            // you need to fallback to an interactive flows such as AcquireTokenInteractive or AcquireTokenByDeviceCode
        //        }
        //        catch (MsalServiceException ex)
        //        {
        //            // Kind of errors you could have (in ex.Message)

        //            // MsalServiceException: AADSTS90010: The grant type is not supported over the /common or /consumers endpoints. Please use the /organizations or tenant-specific endpoint.
        //            // you used common.
        //            // Mitigation: as explained in the message from Azure AD, the authority needs to be tenanted or otherwise organizations

        //            // MsalServiceException: AADSTS70002: The request body must contain the following parameter: 'client_secret or client_assertion'.
        //            // Explanation: this can happen if your application was not registered as a public client application in Azure AD
        //            // Mitigation: in the Azure portal, edit the manifest for your application and set the `allowPublicClient` to `true`
        //        }
        //        catch (MsalClientException ex)
        //        {
        //            // Error Code: unknown_user Message: Could not identify logged in user
        //            // Explanation: the library was unable to query the current Windows logged-in user or this user is not AD or AAD
        //            // joined (work-place joined users are not supported).

        //            // Mitigation 1: on UWP, check that the application has the following capabilities: Enterprise Authentication,
        //            // Private Networks (Client and Server), User Account Information

        //            // Mitigation 2: Implement your own logic to fetch the username (e.g. john@contoso.com) and use the
        //            // AcquireTokenByIntegratedWindowsAuth form that takes in the username

        //            // Error Code: integrated_windows_auth_not_supported_managed_user
        //            // Explanation: This method relies on a protocol exposed by Active Directory (AD). If a user was created in Azure
        //            // Active Directory without AD backing ("managed" user), this method will fail. Users created in AD and backed by
        //            // AAD ("federated" users) can benefit from this non-interactive method of authentication.
        //            // Mitigation: Use interactive authentication
        //        }
        //    }

        //    if (result == null || result.AccessToken == null) throw new System.Exception("Authentication error");

        //    return result.AccessToken;
        //}
        public async Task<string> GetAccessTokenForStudyBuilder()
        {
            AuthenticationResult result = null;
            publicClientApp = await publicClientAppFactory.Create();

            try
            {
                var accounts = await publicClientApp.GetAccountsAsync();
                if (accounts.Any())
                {
                    result = await TryAcquireTokenSilent(publicClientApp, Scopes);
                }
                else
                {
                    result = await publicClientApp.AcquireTokenInteractive(Scopes).ExecuteAsync();
                }
            }
            catch (MsalUiRequiredException)
            {
                result = await publicClientApp.AcquireTokenInteractive(Scopes).ExecuteAsync();
            }
            catch (MsalServiceException ex)
            {
                if (ex.ErrorCode?.ToLower() == "aadsts50173")
                {
                    // Prompt the user to login again
                    result = await publicClientApp.AcquireTokenInteractive(Scopes).ExecuteAsync();
                }
                else
                {
                    throw ex;
                }
            }
            catch (MsalClientException ex)
            {
                throw ex;
            }

            if (result == null || result.AccessToken == null)
                throw new System.Exception("Authentication error");

            return result.AccessToken;
        }

        private async Task<AuthenticationResult> TryAcquireTokenSilent(IPublicClientApplication publicClientApp, string[] scopes)
        {
            try
            {
                return await publicClientApp.AcquireTokenSilent(scopes, (await publicClientApp.GetAccountsAsync()).FirstOrDefault()).ExecuteAsync();
            }
            catch (MsalUiRequiredException)
            {
                throw;
            }
        }
    }
}
