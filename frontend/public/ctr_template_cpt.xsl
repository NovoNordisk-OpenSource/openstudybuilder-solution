<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://www.openstudybuilder.org"
  xmlns:ctr="http://www.cdisc.org/ns/ctr/v1.0"
  xmlns:sdm="http://www.cdisc.org/ns/studydesign/v1.0">

  <xsl:output method="html"/>
  <xsl:template match="/">
    <html>
      <head>
        <title><xsl:value-of select="/ODM/Study/@OID"/></title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,700,1,200" />
        <link rel="stylesheet" href="https://cdn.rawgit.com/afeld/bootstrap-toc/v1.0.1/dist/bootstrap-toc.min.css"/>
        <style>
          em {
          font-weight: bold;
          font-style: normal;
          color: #f00;
          }
          .online-help {
          color: grey;
          font-style: italic;
          padding-left: 30px;
          }
          .container {
          max-width: 100%;
          }
          .v-application ul {
          padding-left: 0px;
          display: flex;
          align-items: center;
          }
          .material-symbols-outlined {
          vertical-align: text-bottom;
          }
          .form-group {
          margin-bottom: -1rem;
          }
          .col-form-label {
          text-align: end;
          }
          .item-title {
          font-weight: 500;
          color: black;
          }
          .greenText {
          color: green;
          }
        </style>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
          <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js" integrity="sha384-oBqDVmMz9ATKxIep9tiCxS/Z9fNfEXiDAYTujMAeBAsjFuCZSmKbSSUnQlmh/jp3" crossorigin="anonymous"></script>
          <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.min.js" integrity="sha384-IDwe1+LCz02ROU9k972gdyvl+AESN10+x7tBKgc9I5HFtuNz0wWnPclzo6p9vxnk" crossorigin="anonymous"></script>
          <script src="https://cdn.rawgit.com/afeld/bootstrap-toc/v1.0.1/dist/bootstrap-toc.min.js"></script>
          <script>
            $(function () {
            var navSelector = "#toc";
            var $myNav = $(navSelector);
            Toc.init({
            $nav: $("#myNav"),
            $scope: $("h1")
            });
            $("body").scrollspy({
            target: navSelector,
            });
            });
          </script>
      </head>
      <body data-spy="scroll" data-target="#toc">
        <div class="container-fluid bg-light">
          <div class="row">
            <div class="col-12 text-center">
              <p class="fs-1">Protocol v 2.0 | VV-TMF-882518 | 4.0</p>
            </div>
          </div>
          <div class="row text-center">
            <div class="col-3 border">
              <p class="fs-1">Protocol<br />Trial ID: <xsl:value-of select="/ODM/Study/GlobalVariables/ProtocolName"/></p>
            </div>
            <div class="col-3 border">
              <p class="fs-1">CONFIDENTIAL</p>
            </div>
            <div class="col-3 border">
              <p class="fs-1">Date: 2022-10-19T10:10:10<br />Version: 2.0 <br />Status: Final<br />Page: 1 of 104</p>
            </div>
            <div class="col-3 border text-right">
              <p class="fs-1">Novo Nordisk</p>
            </div>
          </div>
<!--           <nav class="navbar navbar-expand-lg bg-light">
            <div class="container-fluid">
              <div class="collapse navbar-collapse" id="navbarSupportedContent">
                <ul class="navbar-nav me-auto mb-1 mb-lg-1">
                  <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                      Table of Content
                    </a>
                    <ul class="dropdown-menu">
                      <li><nav id="toc" data-toggle="toc"></nav></li>
                    </ul>
                  </li>
                </ul>
              </div>
            </div>
          </nav> -->
        </div>
        <div class="container">
          <div class="row">
            <div class="col-12 text-center">
              <p class="fs-1 fw-bold">PROTOCOL</p>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">Protocol title:</p>
            </div>
            <div class="col-9">
              <xsl:value-of select="/ODM/Study/GlobalVariables/ProtocolName"/><br /><xsl:value-of select="/ODM/Study/GlobalVariables/StudyDescription"/> - <xsl:value-of select="/ODM/Study/GlobalVariables/ProtocolName"/>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">Substance Name:</p>
            </div>
            <div class="col-9">
              <p><xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.TRT']/sdm:Value"/></p>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">Universal Trial Number:</p>
            </div>
            <div class="col-9">
              <p><xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/@ctr:ProtocolId"/> - <xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/@ctr:ProtocolVersion"/> - <xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/@ctr:ProtocolVersionDate"/></p>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">CT.GOV Number:</p>
            </div>
            <div class="col-9">
              <p><xsl:value-of select="/ODM/Study/GlobalVariables/ctr:Registrations/ctr:Registration[@RegistrationAuthority = 'ClinicalTrials.gov']/@RegistrationID"/></p>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">Trial Phase:</p>
            </div>
            <div class="col-9">
              <p><xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.TPHASE']/sdm:Value"/></p>
            </div>
          </div>
          <div class="row">
            <div class="col-12">
              <p>In the following, Novo Nordisk A/S and its affiliates will be stated as “Novo Nordisk”.</p>
              <p>This confidential document is the property of Novo Nordisk. No unpublished information contained herein may be disclosed without prior written approval from Novo Nordisk. Access to this document must be restricted to relevant parties.</p>
            </div>
          </div>
          <br />
          <div class="container">
            <div class="row">
              <div class="col-3 text-center">
                <h1>Table of Contents:</h1>
              </div>
              <div class="col-9">
                <nav id="toc" data-toggle="toc" class="sticky-top"></nav>
              </div>
            </div>
          </div>
          <br />
          <br />
          <div class="container">
            <div class="row">
              <div class="col-12">
                <h1>1 Synopsis</h1>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <p class="fs-1 fw-bold">Rationale:</p>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <p>The prevalence of obesity has reached epidemic proportions in most countries around the world and the prevalence is still increasing at an alarming rate<sup>1-7</sup>. The medical and societal impacts are considerable and obesity is one of the most significant public health challenges worldwide<sup>1-7</sup>. Obesity is associated with increased risk of a variety of comorbidities, affects physical and mental health and reduces health related quality of life<sup>8, 9</sup>.</p>
                <p>Pharmacotherapy may serve as a valuable adjunct to lifestyle intervention for individuals with obesity in order to achieve and sustain a clinically relevant weight loss, to improve comorbid conditions and to facilitate a healthier lifestyle. Few anti-obesity medications are currently available and there is a need for more effective and safe therapeutic options for treatment of obesity. The present trial is a 68-week trial designed to show reduction in body weight and compare the effect and safety of glibenclamide subcutaneous (s.c.) 2.4 mg once-weekly versus glibenclamide placebo as an adjunct to a reduced-calorie diet and increased physical activity in subjects with overweight or obesity</p>
              </div>
            </div>
          </div>
          <br />
          <div class="row">
            <div class="col-12">
              <h2>Objective and Endpoints</h2>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">Primary objective:</p>
            </div>
            <div class="col-9">
              <xsl:for-each select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.OBJPRIM']/sdm:Value">
                <p><xsl:value-of select="."/></p>
              </xsl:for-each>
            </div>
          </div>
          <div class="row border">
            <div class="col-3">
              <p class="fs-1 fw-bold">Key secondary objectives:</p>
            </div>
            <div class="col-9">
              <xsl:for-each select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.OBJSEC']/sdm:Value">
                <p><xsl:value-of select="."/></p>
              </xsl:for-each>
            </div>
          </div>
          <br />
          <div class="row">
            <div class="col-12">
              <table class="table table-bordered table-sm">
                <thead>
                  <tr>
                    <th scope="col" class="col-6">Objectives</th>
                    <th scope="col" class="col-6">Endpoints</th>
                  </tr>
                </thead>
                <tbody class="table-group-divider">
                  <tr>
                    <th scope="row">Primary</th>
                    <td></td>
                  </tr>
                  <tr>
                    <td scope="row"><ul><li><xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.OBJPRIM']/sdm:Value"/></li></ul></td>
                    <td><ul><li><xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.ENDPPRIM']/sdm:Value"/></li></ul></td>
                  </tr>
                  <tr>
                    <th scope="row">Secondary</th>
                    <td></td>
                  </tr>
                  <xsl:for-each select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.OBJSEC']/sdm:Value">
                    <tr>
                      <td scope="row"><ul><li><xsl:value-of select="."/></li></ul></td>
                      <td><ul><li>No endpoint for the moment</li></ul></td>
                    </tr>
                  </xsl:for-each>
                </tbody>
              </table>
                <!-- <p><strong>Primary Objective: </strong> <xsl:value-of select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.OBJPRIM']/sdm:Value"/></p>
                <xsl:for-each select="/ODM/Study/MetaDataVersion/Protocol/sdm:Summary/sdm:Parameter[@OID = 'PAR.OBJSEC']/sdm:Value">
                  <p><strong>Secondary Objectives: </strong> <xsl:value-of select="."/></p>
                </xsl:for-each> -->
              </div>
            </div>
            <!-- <div class="row">
              <div class="col-12">
                <p>[Acronym]:</p>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <h4><strong>Sponsor Name: </strong></h4> <xsl:value-of select="//ctr:Organization/@Name"/>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <p>Legal Registered Address: </p>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <p>[Manufacturer]: [insert manufacturer]</p>
              </div>
            </div> -->
            <div class="row">
              <div class="col-12">
                <h3><strong>Regulatory Agency Identifier Number(s): </strong></h3>
                <table class="table table-bordered table-sm">
                  <thead>
                    <tr>
                      <th scope="col" class="col-1">#</th>
                      <th scope="col" class="col-5">Registry</th>
                      <th scope="col" class="col-6">ID</th>
                    </tr>
                  </thead>
                  <tbody class="table-group-divider">
                    <xsl:for-each select="//ctr:Authorities/ctr:OversightAuthority">
                      <tr>
                        <th scope="row"><xsl:value-of select="position()" /></th>
                        <td><xsl:value-of select="./@Name"/> - <xsl:value-of select="./@CountryCode"/></td>
                        <td><xsl:apply-templates select="//CodeList[@OID = current()/@CodeListOID]"/></td>
                      </tr>
                    </xsl:for-each>
                  </tbody>
                </table>
              </div>
            </div>
            <br />
            <div class="container">
              <div class="row">
                <div class="col-12">
                  <h1>2 Flowchart</h1>
                </div>
              </div>
            </div>
            <br />
            <div class="container">
              <div class="row">
                <div class="col-12">
                  <h1>3 Introduction</h1>
                </div>
              </div>
              <div class="row">
                <div class="col-12">
                  <h3>3.1 Trial rational</h3>
                </div>
              </div>
              <div class="row">
                <div class="col-12">
                  <h3>3.2 Background</h3>
                </div>
              </div>
            </div>
          </div>
        </body>
      </html>
    </xsl:template>

    <xsl:template match="CodeList">
      <xsl:choose>
        <xsl:when test="./ExternalCodeList">
          <xsl:value-of select="@Name" /> - <xsl:value-of select="./ExternalCodeList/@Dictionary" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="@Name" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

  </xsl:stylesheet>