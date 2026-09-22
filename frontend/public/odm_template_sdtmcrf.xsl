<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://openstudybuilder.org">

  <xsl:output method="html"/>
  <xsl:template match="/">
    <html>
      <head>
        <title><xsl:value-of select="/ODM/Study/@OID"/></title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" />
        <style>
          em {
          font-weight: bold;
          font-style: normal;
          color: #f00;
          }
          .v-application {
          font-family: "Open Sans", serif;
          line-height: 1.2;
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
          .form-group {
          margin-bottom: -1rem;
          }
          .material-symbols-outlined {
          vertical-align: text-bottom;
          }
          .form-control-disabled {
          pointer-events: none;
          }
          .col-form-label {
          text-align: end;
          }
          .oidinfo {
          color: red;
          font-style: normal;
          font-size: 12px;
          }
          .badge {
          font-weight: 500;
          }
          .badge-ig {
          display: inline-block;
          padding: 0.25em 0.4em;
          font-size: 75%;
          font-weight: 600;
          line-height: 1;
          text-align: center;
          white-space: nowrap;
          vertical-align: baseline;
          border-radius: 0.25rem;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
          }
          input[type="radio"] {
          margin-top: 4px;
          vertical-align: middle;
          }
          .greenItem {
          color: green;
          }
          .blackItem {
          color: black;
          }
          .alert {
          position: relative;
          padding: 0.4rem 0.8rem;
          margin-bottom: 0.2rem;
          border: 1px solid #0000001c;
          border-radius: 0.2rem;
          }
          .alert-green {
          color: green;
          }
        </style>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js" integrity="sha384-oBqDVmMz9ATKxIep9tiCxS/Z9fNfEXiDAYTujMAeBAsjFuCZSmKbSSUnQlmh/jp3" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.min.js" integrity="sha384-IDwe1+LCz02ROU9k972gdyvl+AESN10+x7tBKgc9I5HFtuNz0wWnPclzo6p9vxnk" crossorigin="anonymous"></script>
      </head>
      <body>
        <div class="container">
          <div class="row">
            <div class="col-9">
              <h3><xsl:value-of select="/ODM/Study/GlobalVariables/StudyName"/></h3>
            </div>
            <div class="col-3">
              <h3>Annotated CRF [MSG2.0]</h3>
            </div>
          </div>
          <xsl:apply-templates select="/ODM/Study/MetaDataVersion/FormDef"/>
        </div>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="ItemDef">
    <xsl:param name="domainNiv" />
    <xsl:param name="itemCondition" />
    <xsl:param name="domainBckg" />
    <xsl:variable name="displayType">
      <xsl:choose>
        <xsl:when test="./Alias/@Context = 'CTDisplay'">Checkbox</xsl:when>
        <xsl:when test="./@osb:allowsMultiChoice = 'True'">Checkbox</xsl:when>
        <xsl:otherwise>Radio</xsl:otherwise> <!-- default value -->
      </xsl:choose>
    </xsl:variable>

    <div class="container">
      <xsl:choose>
        <xsl:when test="./@DataType = 'comment'"> <!-- Title -->
          <div class="row">
            <div class="col-4 border text-right" /> <!-- Item lable column -->
            <div class="col-8 border text-left">
              <xsl:choose>
                <xsl:when test="./Question">
                  <xsl:choose>
                    <xsl:when test="$itemCondition != 'null'">
                      <span class="material-symbols-outlined alert-green">subdirectory_arrow_right</span>&#160;
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="'No'" />
                        <xsl:with-param name="sdvItem" select="'No'" />
                      </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="'No'" />
                        <xsl:with-param name="sdvItem" select="'No'" />
                      </xsl:apply-templates>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="@Name" />
                </xsl:otherwise>
              </xsl:choose>
              <xsl:choose>
                <xsl:when test="./Alias/@Context = 'CDASH/SDTM'">
                  <xsl:for-each select="./Alias[@Context = 'CDASH/SDTM']">
                    <br />
                    <xsl:call-template name="splitter">
                      <xsl:with-param name="remaining-string"  select="./@Name"/>
                      <xsl:with-param name="pattern" select="'|'"/>
                      <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:choose>
                    <xsl:when test="@SDSVarName != 'None'">
                      <br />
                      <xsl:call-template name="splitter">
                        <xsl:with-param name="remaining-string"  select="@SDSVarName"/>
                        <xsl:with-param name="pattern"  select="'|'"/>
                        <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                      </xsl:call-template>
                    </xsl:when>
                  </xsl:choose>
                </xsl:otherwise>
              </xsl:choose>
            </div>
          </div>
        </xsl:when>
        <xsl:otherwise> <!-- Not a title -->
          <div class="row">
            <div class="col-1 border text-left">
              <xsl:if test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
                <em> * </em>
              </xsl:if>
              <span class="material-symbols-outlined">lock</span>
              <span class="material-symbols-outlined">account_tree</span>
            </div>
            <div class="col-3 border text-right"> <!-- Item lable column -->
              <xsl:choose>
                <xsl:when test="./Question">
                  <xsl:choose>
                    <xsl:when test="$itemCondition != 'null'">
                      &#160;&#160;<span class="material-symbols-outlined alert-green">subdirectory_arrow_right</span>&#160;
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:locked" />
                        <xsl:with-param name="sdvItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:sdv" />
                        <xsl:with-param name="mandatoryItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory" />
                      </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:locked" />
                        <xsl:with-param name="sdvItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:sdv" />
                        <xsl:with-param name="mandatoryItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory" />
                      </xsl:apply-templates>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="@Name" />
                </xsl:otherwise>
              </xsl:choose>
              <br /><span class="oidinfo">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />]</span>
              <xsl:choose>
                <xsl:when test="./@osb:instruction != 'None'">
                  <div class="alert alert-success text-left" role="alert">
                    <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:instruction" />
                  </div>
                </xsl:when>
              </xsl:choose>
            </div>
            <!-- Item field column -->
            <xsl:choose>
              <xsl:when test="MeasurementUnitRef">
                <div class="col-4 border text-left">
                  <div class="input-group">
                    <xsl:choose>
                      <xsl:when test="./@Origin = 'Derived Value'">
                        <input type="{@DataType}" class="form-control" id="item{@OID}" name="{@Name}" min="4" max="40" size="{@Length}" aria-describedby="basic-addon2" disabled="disabled" />
                        <span class="input-group-text" id="item{@OID}"><xsl:value-of select="@Length" /> digit(s)</span>
                      </xsl:when>
                      <xsl:otherwise>
                        <input type="{@DataType}" class="form-control" id="item{@OID}" name="{@Name}" min="4" max="40" size="{@Length}" aria-describedby="basic-addon2" />
                        <span class="input-group-text" id="item{@OID}"><xsl:value-of select="@Length" /> digit(s)</span>
                      </xsl:otherwise>
                    </xsl:choose>
                  </div>
                  <xsl:choose>
                    <xsl:when test="./Alias/@Context = 'CDASH/SDTM'">
                      <xsl:for-each select="./Alias[@Context = 'CDASH/SDTM']">
                        <xsl:call-template name="splitter">
                          <xsl:with-param name="remaining-string"  select="./@Name"/>
                          <xsl:with-param name="pattern" select="'|'"/>
                          <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                        </xsl:call-template>
                      </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:call-template name="splitter">
                        <xsl:with-param name="remaining-string"  select="@SDSVarName"/>
                        <xsl:with-param name="pattern"  select="'|'"/>
                        <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                      </xsl:call-template>
                    </xsl:otherwise>
                  </xsl:choose>
                </div>
                <div class="col-1 border text-left">
                  Unit :
                </div>
                <div class="col-3 border text-left">
                  <xsl:for-each select="MeasurementUnitRef">
                    <input type="radio" id="{@MeasurementUnitOID}" name="{../@OID}" value="{@MeasurementUnitOID}" />
                    <label for="contactChoice1">&#160;
                      <xsl:apply-templates select="//BasicDefinitions/MeasurementUnit[@OID = current()/@MeasurementUnitOID]/Symbol" />
                    </label>&#160;<span class="oidinfo"> [OID=<xsl:value-of select="@MeasurementUnitOID" />, Version=<xsl:value-of select="//BasicDefinitions/MeasurementUnit[@OID = current()/@MeasurementUnitOID]/@osb:version" />]</span>
                    <br />
                  </xsl:for-each>
                </div>
              </xsl:when>
              <xsl:otherwise>
                <div class="col-8 border text-left">
                  <xsl:choose>
                    <xsl:when test="CodeListRef">
                      <xsl:for-each select="CodeListRef">
                        <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/CodeListItem">
                          <input type="{$displayType}" id="{@CodedValue}" name="{../@OID}" value="{@CodedValue}" />
                          <label for="contactChoice2">&#160;<xsl:apply-templates select="Decode"/>&#160;[<xsl:value-of select="@CodedValue" />]</label>&#160;<span class="oidinfo">[OID=<xsl:value-of select="@osb:oid" />, Version=<xsl:value-of select="@osb:version" />]</span><br />
                        </xsl:for-each>
                        <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/EnumeratedItem">
                          <input type="{$displayType}" id="{@CodedValue}" name="{../@OID}" value="{@CodedValue}" />
                          <label for="contactChoice2">&#160;<xsl:value-of select="@CodedValue" /></label><br />
                        </xsl:for-each>
                        <span class="oidinfo">[OID=<xsl:value-of select="@CodeListOID" />, Version=<xsl:value-of select="//CodeList[@OID = current()/@CodeListOID]/@osb:version" />]</span>
                        <xsl:choose>
                          <xsl:when test="../Alias/@Context = 'CDASH/SDTM'">
                            <br />
                            <xsl:for-each select="../Alias[@Context = 'CDASH/SDTM']">
                              <xsl:call-template name="splitter">
                                <xsl:with-param name="remaining-string"  select="./@Name"/>
                                <xsl:with-param name="pattern" select="'|'"/>
                                <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                              </xsl:call-template>
                            </xsl:for-each>
                          </xsl:when>
                          <xsl:otherwise>
                            <br />
                            <xsl:call-template name="splitter">
                              <xsl:with-param name="remaining-string"  select="../@SDSVarName"/>
                              <xsl:with-param name="pattern"  select="'|'"/>
                              <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                            </xsl:call-template>
                          </xsl:otherwise>
                        </xsl:choose>
                      </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                      <div class="input-group">
                        <xsl:choose>
                          <xsl:when test="@DataType = 'boolean'">
                            <input type="checkbox" id="item{@OID}" name="{@Name}" aria-describedby="basic-addon2"/>
                            <!-- &#160;<label for="{@name}"><xsl:value-of select="@Name" /></label> -->
                          </xsl:when>
                          <xsl:otherwise>
                            <input type="{@DataType}" class="form-control" id="item{@OID}" name="{@Name}" min="4" max="40" size="{@Length}" aria-describedby="basic-addon2"/>
                            <span class="input-group-text" id="item{@OID}"><xsl:value-of select="@Length" /> digit(s)</span>
                          </xsl:otherwise>
                        </xsl:choose>
                      </div>
                      <xsl:choose>
                        <xsl:when test="./Alias/@Context = 'CDASH/SDTM'">
                          <xsl:for-each select="./Alias[@Context = 'CDASH/SDTM']">
                            <xsl:call-template name="splitter">
                              <xsl:with-param name="remaining-string"  select="./@Name"/>
                              <xsl:with-param name="pattern" select="'|'"/>
                              <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                            </xsl:call-template>
                          </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>
                          <xsl:call-template name="splitter">
                            <xsl:with-param name="remaining-string"  select="@SDSVarName"/>
                            <xsl:with-param name="pattern"  select="'|'"/>
                            <xsl:with-param name="domainbgcolor" select="$domainBckg"/>
                          </xsl:call-template>
                        </xsl:otherwise>
                      </xsl:choose>
                      <xsl:choose>
                        <xsl:when test="./@osb:sponsorInstruction != 'None'">
                          <div class="alert alert-danger" role="alert">
                            <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:sponsorInstruction" />
                          </div>
                        </xsl:when>
                      </xsl:choose>
                    </xsl:otherwise>
                  </xsl:choose>
                </div>
              </xsl:otherwise>
            </xsl:choose>
          </div>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template match="ItemGroupDef">
    <xsl:variable name="domainLevel" select="../FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@OrderNumber+1" />
    <xsl:variable name="domainBg">
      <xsl:choose>
        <xsl:when test="./@Domain">
          <xsl:for-each select="./osb:DomainColor">
            <xsl:value-of select="." />
          </xsl:for-each>
        </xsl:when>
        <xsl:when test="./Alias/@Context = 'CDASH/SDTM'">
          <xsl:for-each select="../Alias[@Context = 'CDASH/SDTM']">
            <xsl:choose>
              <xsl:when test="contains(./@Name, 'Note')">
                <xsl:value-of select="substring-after('Note:',@Name)" />
                <xsl:value-of select="':#ffffff;'" />
              </xsl:when>
              <xsl:when test="position() = 4">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of select="':#ffbf9c;'" />
              </xsl:when>
              <xsl:when test="position() = 3">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of select="':#96ff96;'" />
              </xsl:when>
              <xsl:when test="position() = 2">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of select="':#ffff96;'" />
              </xsl:when>
              <xsl:when test="position() = 1">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of select="':#bfffff;'" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of select="':#96ff96;'" />
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:when>
      </xsl:choose>
    </xsl:variable>
    <div class="alert alert-dark" role="alert">
      <div class="row">
        <div class="col-3">
          <h4>
            <xsl:value-of select="$domainLevel"/>: <xsl:value-of select="./Description/TranslatedText" />&#160;
            <xsl:if test="//FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@Mandatory = 'Yes'">
              <em> * </em>
            </xsl:if>
          </h4>
          <span class="oidinfo">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />]</span>
        </div>
        <div class="col-9">
          <xsl:choose>
            <xsl:when test="./osb:SdtmMetadata/osb:Sdtm">
              <xsl:for-each select="./osb:SdtmMetadata/osb:Sdtm">
                <h4><span class="badge" style="background-color:{@DomainColor} border: 1px solid #000;"><b><xsl:value-of select="./@SdtmDomain" /></b></span>&#160;</h4>
              </xsl:for-each>
            </xsl:when>
            <xsl:when test="./Alias/@Context = 'CDASH/SDTM'">
              <h5>
                <xsl:for-each select="./Alias[@Context = 'CDASH/SDTM']">
                  <xsl:call-template name="IGsplitter">
                    <xsl:with-param name="remaining-string"  select="./@Name"/>
                    <xsl:with-param name="pattern"  select="'|'"/>
                    <xsl:with-param name="domainbgcolor" select="$domainBg"/>
                  </xsl:call-template>
                </xsl:for-each>
              </h5>
            </xsl:when>
            <xsl:otherwise>
              <h5>
                <xsl:call-template name="IGsplitter">
                  <xsl:with-param name="remaining-string"  select="./@Domain"/>
                  <xsl:with-param name="pattern"  select="'|'"/>
                  <xsl:with-param name="domainbgcolor" select="$domainBg"/>
                </xsl:call-template>
              </h5>
            </xsl:otherwise>
          </xsl:choose>
        </div>
      </div>
      <div class="row">
        <div class="col-12">
          <xsl:choose>
            <xsl:when test="./@osb:instruction != 'None'">
              <div class="alert alert-success" role="alert">
                <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:instruction" />
              </div>
            </xsl:when>
          </xsl:choose>
          <xsl:choose>
            <xsl:when test="./@osb:sponsorInstruction != 'None'">
              <div class="alert alert-danger" role="alert">
                <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:sponsorInstruction" />
              </div>
            </xsl:when>
          </xsl:choose>
          <xsl:choose>
            <xsl:when test="./Alias/@Context = 'ImplementationNotes'">
              <div class="alert alert-danger" role="alert">
                <xsl:for-each select="./Alias[@Context = 'ImplementationNotes']">
                  <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of disable-output-escaping="yes" select="./@Name" />
                </xsl:for-each>
              </div>
            </xsl:when>
          </xsl:choose>
        </div>
      </div>
      <xsl:for-each select="ItemRef">
        <xsl:sort select="@OrderNumber"/>
        <xsl:apply-templates select="//ItemDef[@OID = current()/@ItemOID]">
          <xsl:with-param name="domainNiv" select="$domainLevel"/>
          <xsl:with-param name="domainBckg" select="$domainBg"/>
          <xsl:with-param name="itemCondition" select="current()/@CollectionExceptionConditionOID"/>
        </xsl:apply-templates>
      </xsl:for-each>
    </div>
  </xsl:template>

  <xsl:template match="FormDef" >
    <ul class="nav nav-tabs nav-fill">
      <li class="nav-item">
        <a class="nav-link active" href="#">
          <h3><xsl:value-of select="@Name" /></h3>
        </a>
      </li>
      <li class="nav-item">
        <a class="nav-link disabled text-left" href="#" tabindex="-1" aria-disabled="true"><span class="blackItem">Black label</span> are Mandatory (otherwise <span class="greenItem">Green</span>)</a>
        <a class="nav-link disabled text-left" href="#" tabindex="-1" aria-disabled="true"><span class="material-symbols-outlined">
          lock</span> Lock</a>
        </li>
        <li class="nav-item">
          <a class="nav-link disabled text-right" href="#" tabindex="-1" aria-disabled="true"><em>*</em> Data Entry Required</a>
          <a class="nav-link disabled text-right" href="#" tabindex="-1" aria-disabled="true"><span class="material-symbols-outlined">
            account_tree</span> Source Data Verification (SDV)</a>
          </li>
        </ul>
        <xsl:choose>
          <xsl:when test="./@osb:instruction != 'None'">
            <div class="alert alert-success" role="alert">
              <span class="material-symbols-outlined">help</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:instruction" />
            </div>
          </xsl:when>
        </xsl:choose>
        <xsl:choose>
          <xsl:when test="./@osb:sponsorInstruction != 'None'">
            <div class="alert alert-danger" role="alert">
              <span class="material-symbols-outlined">emergency_home</span>&#160;<xsl:value-of disable-output-escaping="yes" select="@osb:sponsorInstruction" />
            </div>
          </xsl:when>
        </xsl:choose>
        <xsl:for-each select="ItemGroupRef">
          <xsl:sort select="current()/@OrderNumber"/>
          <xsl:apply-templates select="//ItemGroupDef[@OID = current()/@ItemGroupOID]"/><br />
        </xsl:for-each>
        <br /><br />
      </xsl:template>

      <xsl:template match="Description">
        <xsl:choose>
          <xsl:when test="TranslatedText">
            <span class="online-help">
              <span class="material-symbols-outlined">info</span>
              <xsl:value-of select="TranslatedText" />
            </span>
          </xsl:when>
        </xsl:choose>
      </xsl:template>

      <xsl:template match="Question">
        <xsl:param name="lockItem"/>
        <xsl:param name="sdvItem"/>
        <xsl:param name="mandatoryItem"/>
        <xsl:choose>
          <xsl:when test="$mandatoryItem = 'No'">
            <span class="greenItem"><xsl:value-of select="TranslatedText" />&#160;</span>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="TranslatedText" />&#160;
          </xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
          <xsl:when test="($lockItem = 'Yes') and ($sdvItem = 'Yes')">
            <span class="material-symbols-outlined">lock</span>&#160;<span class="material-symbols-outlined">account_tree</span>
          </xsl:when>
          <xsl:when test="$lockItem = 'Yes'">
            <span class="material-symbols-outlined">lock</span>
          </xsl:when>
          <xsl:when test="$sdvItem = 'Yes'">
            <span class="material-symbols-outlined">account_tree</span>
          </xsl:when>
          <xsl:otherwise>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:template>

      <xsl:template match="Decode">
        <xsl:value-of select="TranslatedText" />
      </xsl:template>

      <xsl:template match="Symbol">
        <xsl:value-of select="TranslatedText" />
      </xsl:template>

      <xsl:template name="IGsplitter">
        <xsl:param name="remaining-string"/>
        <xsl:param name="pattern"/>
        <xsl:param name="domainbgcolor"/>
        <xsl:variable name="itemBg">
          <xsl:choose>
            <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
              <xsl:value-of select="substring-after($domainbgcolor,substring($remaining-string,1,3))" />
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="'#bfffff;'" />
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:choose>
          <xsl:when test="contains($remaining-string,$pattern)">
            <split-item>
              <xsl:choose>
                <xsl:when test="contains($remaining-string,'Note:')">
                  <span class="badge-ig" style="background-color:#ffffff; border: 1px dotted #000; color:black;">
                    <xsl:value-of select = "normalize-space($remaining-string,$pattern)"/>
                  </span><br />
                </xsl:when>
                <xsl:otherwise>
                  <span class="badge-ig" style="background-color:{$itemBg} border: 1px solid #000; color:black;">
                    <xsl:value-of select = "normalize-space(concat(substring-before(substring-before($remaining-string,$pattern),':'),' (', substring-after(substring-before($remaining-string,$pattern),':'),')'))"/>
                  </span><br />
                </xsl:otherwise>
              </xsl:choose>
            </split-item>
            <xsl:call-template name="IGsplitter">
              <xsl:with-param name="remaining-string"  select="substring-after($remaining-string,$pattern)"/>
              <xsl:with-param name="pattern"  select="$pattern"/>
              <xsl:with-param name="domainbgcolor" select="$itemBg"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <split-item>
              <xsl:choose>
                <xsl:when test="contains($remaining-string,'Note:')">
                  <span class="badge-ig" style="background-color:#ffffff; border: 1px dotted #000; color:black;">
                    <xsl:value-of select = "normalize-space($remaining-string)"/>
                  </span><br />
                </xsl:when>
                <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                  <span class="badge-ig" style="background-color:#ffffff; border: 1px dotted #000; color:black;">
                    <xsl:value-of select = "normalize-space($remaining-string)"/>
                  </span><br />
                </xsl:when>
                <xsl:when test="$remaining-string != ''">
                  <span class="badge-ig" style="background-color:{$itemBg} border: 1px solid #000; color:black;">
                    <xsl:value-of select = "normalize-space(concat(substring-before($remaining-string,':'),' (', substring-after($remaining-string,':'),')'))" />
                  </span><br />
                </xsl:when>
                <xsl:otherwise>
                </xsl:otherwise>
              </xsl:choose>
            </split-item>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:template>

      <xsl:template name="splitter">
        <xsl:param name="remaining-string"/>
        <xsl:param name="pattern"/>
        <xsl:param name="domainbgcolor"/>
        <xsl:variable name="itemBg">
          <xsl:choose>
            <xsl:when test="contains($remaining-string,'Note')">
              <xsl:value-of select="'#ffffff;'" />
            </xsl:when>
            <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
              <xsl:value-of select="substring(substring-after($domainbgcolor,substring($remaining-string,1,2)),2,8)" />
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="'#bfffff;'" />
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:variable name="remainingstrg">
          <xsl:choose>
            <xsl:when test="contains($remaining-string,':')">
              <xsl:value-of select="substring-after($remaining-string,':')" />
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$remaining-string" />
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:choose>
          <xsl:when test="contains($remainingstrg,$pattern)">
            <split-item>
              <xsl:choose>
                <xsl:when test="contains($remaining-string,'Note')">
                  <span class="badge" style="background-color:{$itemBg} border: 1px dotted #000; color:black;">
                    <xsl:value-of select = "normalize-space(substring-before($remainingstrg,$pattern))"/>
                  </span>&#160;
                </xsl:when>
                <xsl:otherwise>
                  <span class="badge" style="background-color:{$itemBg} border: 1px solid #000; color:black;">
                    <xsl:value-of select = "normalize-space(substring-before($remainingstrg,$pattern))"/>
                  </span>&#160;
                </xsl:otherwise>
              </xsl:choose>
            </split-item>
            <xsl:call-template name="splitter">
              <xsl:with-param name="remaining-string"  select="substring-after($remainingstrg,$pattern)"/>
              <xsl:with-param name="pattern"  select="$pattern"/>
              <xsl:with-param name="domainbgcolor" select="$domainbgcolor"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <split-item>
              <xsl:choose>
                <xsl:when test="contains($remaining-string,'Note')">
                  <span class="badge" style="background-color:{$itemBg} border: 1px dotted #000; color:black;">
                    <xsl:value-of select = "normalize-space($remainingstrg)"/>
                  </span>&#160;
                </xsl:when>
                <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                  <span class="badge" style="background-color:#ffffff; border: 1px dotted #000; color:black;">
                    <xsl:value-of select = "normalize-space($remainingstrg)"/>
                  </span>&#160;
                </xsl:when>
                <xsl:otherwise>
                  <span class="badge" style="background-color:{$itemBg} border: 1px solid #000; color:black;">
                    <xsl:value-of select = "normalize-space($remainingstrg)"/>
                  </span>&#160;
                </xsl:otherwise>
              </xsl:choose>
            </split-item>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:template>

      <xsl:template name="replace-string">
        <xsl:param name="text"/>
        <xsl:param name="replace"/>
        <xsl:param name="with"/>
        <xsl:choose>
          <xsl:when test="contains($text,$replace)">
            <xsl:value-of select="substring-before($text,$replace)"/>
            <xsl:value-of select="$with"/>
            <xsl:call-template name="replace-string">
              <xsl:with-param name="text" select="substring-after($text,$replace)"/>
              <xsl:with-param name="replace" select="$replace"/>
              <xsl:with-param name="with" select="$with"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$text"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:template>

    </xsl:stylesheet>