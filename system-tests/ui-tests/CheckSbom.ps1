param(
  [string] [Parameter(Mandatory = $true)] $token,
  [string] [Parameter(Mandatory = $true)] $pullRequestId,
  [string] [Parameter(Mandatory = $true)] $projectName,
  [string] [Parameter(Mandatory = $true)] $repositoryName,
  $user = "",
  $baseurl = "https://dev.azure.com/orgremoved",
  $threadId = "1"
)

# Base64-encodes the Personal Access Token (PAT) appropriately
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $user, $token)))
write-host $WorkitemType

$uri = "https://dev.azure.com/orgremoved/Clinical-MDR/_apis/git/repositories?api-version=7.0"
Write-Host $uri
$result = Invoke-RestMethod -Uri $uri -Method Get -Headers @{Authorization = ("Basic {0}" -f $base64AuthInfo) }

For ($i = 0; $i -le $result.value.Length; $i++) {
    if ($result.value[$i].name -eq $repositoryName) {
        $repositoryid = $result.value[$i].id
    }
}

function CreateJsonBody {

    $value = @"
{
  "comments": [
    {
      "parentCommentId": 0,
      "content": "NOTE: Changes have been detected to sbom.md. License changes should be verified, so we make sure we are still compliant with licenses and change our guidance text if necessary due to new/changed dependencies. Contact MT and when the next steps have been decided, then resolve this comment so the PR can be completed.",
      "commentType": 1
    }
  ],
  "status": 1
}
"@

    return $value
}

$json = CreateJsonBody

$uri = "$baseurl/$projectName/_apis/git/repositories/$repositoryId/pullRequests/$pullRequestId/threads?api-version=7.0"
Write-Host $uri
$result = Invoke-RestMethod -Uri $uri -Method Post -Body $json -ContentType "application/json" -Headers @{Authorization = ("Basic {0}" -f $base64AuthInfo) }


