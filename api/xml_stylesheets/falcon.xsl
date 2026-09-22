<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://openstudybuilder.org"
  xmlns:office="urn:schemas-microsoft-com:office:office"
  xmlns:word="urn:schemas-microsoft-com:office:word"
  xmlns="http://www.w3.org/TR/REC-html40">

  <xsl:output method="html" />
  <xsl:template match="/">
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word">
      <head>
        <meta charset="UTF-8" />
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB" crossorigin="anonymous" />
        <title>
          <xsl:value-of select="/ODM/Study/@OID" />
        </title>
        <style>
          body {
          font-family: Arial;
          background-color: #ffffff;
          margin: 0px;
          }

          h1, h2, h3, h4, h5 {
          margin-top: 2px;
          margin-bottom: 1px;
          padding: 3px;
          }

          .btn {
          background-color: #1a3172 !important;
          border-color: #1a3172 !important;
          }

          .btn-clicked {
          background-color: #BDD6EE !important;
          border-color: #BDD6EE !important;
          color: #fff !important;
          }

          em {
          font-weight: bold;
          font-style: normal;
          color: #f00;
          }

          .badge {
          display: inline-block;
          margin: 0.2em;
          padding: 2px 4px;
          font-size: 70%;
          font-weight: 550;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 5px;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
          }

          .badge-ig {
          display: inline-block;
          margin: 0.2em;
          padding: 6px 8px;
          font-size: 80%;
          font-weight: 600;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 8px;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
          }

          .oidinfo {
          color: red !important;
          font-style: normal;
          font-size: 12px;
          }

          @media print {
          .page-break {
          page-break-before: always;
          break-before: page;
          }
          thead { display: table-header-group; }
          tfoot { display: table-footer-group; }
          .repeat-on-each-page { display: table-row-group; }
          }

          @page Section1 {size:841.7pt 595.45pt;mso-page-orientation:landscape;margin:1.25in 1.0in 1.25in 1.0in;mso-header-margin:.5in;mso-footer-margin:.5in;mso-paper-source:0;}

          div.Section2 {page:Section2;}
        </style>
        <xsl:comment>[if gte mso 9]&gt;
          &lt;style&gt;
          .d-print-none {
          mso-hide: all;
          display: none !important;
          visibility: hidden !important;
          height: 0 !important;
          width: 0 !important;
          overflow: hidden !important;
          font-size: 0 !important;
          line-height: 0 !important;
          margin: 0 !important;
          padding: 0 !important;
          }
          &lt;/style&gt;
          &lt;![endif]</xsl:comment>
        </head>
        <body>
          <div class="Section1">
            <table style="border-collapse: collapse; width: 100%; margin: 0 auto; background: #fff;">
              <tbody>
                <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
                <div class="d-print-none" align="right">
                  <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="collapse" data-bs-target=".ActivityInstance" onclick="toggleButtonColor(this)">Activity Instances</button>&#160;
                  <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="collapse" data-bs-target=".Cdash" onclick="toggleButtonColor(this)">Source Value</button>&#160;
                  <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="collapse" data-bs-target=".Sdtm" onclick="toggleButtonColor(this)">Sdtm</button>&#160;
                  <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="collapse" data-bs-target=".oid" onclick="toggleButtonColor(this)">Keys</button>
                </div>
                <xsl:comment>&lt;![endif]</xsl:comment>
                <xsl:apply-templates select="/ODM/Study/MetaDataVersion/FormDef" />
              </tbody>
            </table>
          </div>
        </body>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js" integrity="sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI" crossorigin="anonymous"></script>
        <script src="https://code.jquery.com/jquery-3.7.1.slim.min.js" integrity="sha256-kmHvs0B+OpCW5GVHUNjv9rOmY0IvSIRcf7zGUDTDQM8=" crossorigin="anonymous"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
        <script>
          function toggleButtonColor(button) {
          button.classList.toggle('btn-clicked');
          }
        </script>
      </html>
    </xsl:template>

    <xsl:template match="ItemDef">
      <xsl:param name="domainBckg" />

      <xsl:variable name="trBckg">
        <xsl:choose>
          <xsl:when test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:optionalQuestion = 'Yes'">
            <xsl:value-of select="'background-color:#AEAAAA; color:#008000;'" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="'background-color:#E7E6E6; color:#000000;'" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <xsl:variable name="indentLevel" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:indentLevel" />

      <tr style="{$trBckg}">
        <xsl:choose>
          <xsl:when test="./@DataType = 'comment'">
            <td colspan="5" style="border: 1px solid #fff; padding: 2px; width:100%;">
              <h4>
                <xsl:value-of select="@Name" />
              </h4>
            </td>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="firstColor" select="concat('#', substring-before(substring-after($domainBckg, '#'), ' '))" />
            <td style="border: 1px solid #fff; padding: 2px; width:5%;">
              <xsl:if test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
                <em>&#160;*&#160;</em>
              </xsl:if>
            </td>
            <td style="border: 1px solid #fff; padding: 2px; width:30%;">
              <span style="margin-left:{ $indentLevel * 2 }em;">
                <xsl:value-of select="@Name" />
              </span>

              <xsl:for-each select="./osb:ActivityInstance">
                <xsl:call-template name="VendorExtensionActIns">
                  <xsl:with-param name="vendorExtensionContext" select="ActivityInstance" />
                  <xsl:with-param name="vendorExtensionName" select="." />
                </xsl:call-template>
              </xsl:for-each>

              <xsl:for-each select="./Alias[@Context = 'TopicCode']">
                <xsl:call-template name="Alias">
                  <xsl:with-param name="aliasContext" select="@Context" />
                  <xsl:with-param name="aliasName" select="@Name" />
                  <xsl:with-param name="aliasBgcolor" select="'#3496f0'" />
                </xsl:call-template>
              </xsl:for-each>
              <xsl:for-each select="./Alias[@Context = 'AdamCode']">
                <xsl:call-template name="Alias">
                  <xsl:with-param name="aliasContext" select="@Context" />
                  <xsl:with-param name="aliasName" select="@Name" />
                  <xsl:with-param name="aliasBgcolor" select="'#2f2f2f'" />
                </xsl:call-template>
              </xsl:for-each>
              <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
              <div class="oidinfo oid collapse d-print-none">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />, Datatype=<xsl:value-of select="@DataType" />]</div>
              <xsl:comment>&lt;![endif]</xsl:comment>
            </td>
            <td style="border: 1px solid #fff; padding: 2px; width:30%;">
              <xsl:for-each select="CodeListRef">
                <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/CodeListItem">
                  <xsl:sort select="@OrderNumber" data-type="number" order="ascending" />
                  <div>
                    <span style="margin-left:{ $indentLevel * 2 }em;">
                      <span style='font-size:30px;'>&#9675;</span>&#160;<xsl:value-of select="@osb:name" />&#160;
                      <xsl:for-each select="@CodedValue">
                        <xsl:call-template name="splitter">
                          <xsl:with-param name="aliasContext" select="'Cdash'" />
                          <xsl:with-param name="remaining-string" select="." />
                          <xsl:with-param name="pattern" select="'|'" />
                          <xsl:with-param name="domainbgcolor" select="$firstColor" />
                        </xsl:call-template>
                      </xsl:for-each>
                    </span>
                  </div>
                  <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
                  <div class="oidinfo oid collapse d-print-none">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />, Datatype=string]</div>
                  <xsl:comment>&lt;![endif]</xsl:comment>
                </xsl:for-each>
                <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/EnumeratedItem">
                  <xsl:sort select="@OrderNumber" data-type="number" order="ascending" />
                  <div>
                    <span style="margin-left:{ $indentLevel * 2 }em;">
                      <span style='font-size:30px;'>&#9675;</span>&#160;<xsl:value-of select="@osb:name" />&#160;
                      <xsl:for-each select="@CodedValue">
                        <xsl:call-template name="splitter">
                          <xsl:with-param name="aliasContext" select="'Cdash'" />
                          <xsl:with-param name="remaining-string" select="." />
                          <xsl:with-param name="pattern" select="'|'" />
                          <xsl:with-param name="domainbgcolor" select="$firstColor" />
                        </xsl:call-template>
                      </xsl:for-each>
                    </span>
                  </div>
                  <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
                  <div class="oidinfo oid collapse d-print-none">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />]</div>
                  <xsl:comment>&lt;![endif]</xsl:comment>
                </xsl:for-each>
                <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
                <div class="oidinfo oid collapse d-print-none">[OID=<xsl:value-of select="@CodeListOID" />, Version=<xsl:value-of select="//CodeList[@OID = current()/@CodeListOID]/@osb:version" />, Datatype=<xsl:value-of select="//CodeList[@OID = current()/@CodeListOID]/@DataType" />]</div>
                <xsl:comment>&lt;![endif]</xsl:comment>
              </xsl:for-each>
              <xsl:for-each select="./Alias[@Context = 'wordFormat']">
                <xsl:value-of disable-output-escaping="yes" select="@Name" />&#160;
              </xsl:for-each>
              <xsl:choose>
                <xsl:when test="./osb:DesignNotes">
                  <div class="alert alert-danger sponsor collapse" role="alert">
                    <span class="material-symbols-outlined">emergency_home</span>
                    <xsl:value-of disable-output-escaping="yes" select="./osb:DesignNotes" />
                  </div>
                </xsl:when>
              </xsl:choose>
            </td>
            <td style="border: 1px solid #fff; padding: 2px; width:30%;">
              <h5>
                <xsl:call-template name="splitter">
                  <xsl:with-param name="aliasContext" select="'Sdtm'" />
                  <xsl:with-param name="remaining-string" select="@SDSVarName" />
                  <xsl:with-param name="pattern" select="'|'" />
                  <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                </xsl:call-template>
                <xsl:for-each select="./Alias[@Context = 'Cdash']">
                  <xsl:call-template name="splitter">
                    <xsl:with-param name="aliasContext" select="@Context" />
                    <xsl:with-param name="remaining-string" select="./@Name" />
                    <xsl:with-param name="pattern" select="'|'" />
                    <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                  </xsl:call-template>
                </xsl:for-each>
                <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                  <xsl:call-template name="splitter">
                    <xsl:with-param name="aliasContext" select="@Context" />
                    <xsl:with-param name="remaining-string" select="./@Name" />
                    <xsl:with-param name="pattern" select="'|'" />
                    <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                  </xsl:call-template>
                </xsl:for-each>
              </h5>
            </td>
            <td style="border: 1px solid #fff; padding: 2px; width:10%;">
              <xsl:for-each select="./Alias[@Context = 'ctdmIntegration']">
                <xsl:value-of disable-output-escaping="yes" select="@Name" />
              </xsl:for-each>
              <xsl:if test="@Length">
                <span><br /><xsl:value-of select="@Length" /> digit(s)</span>
              </xsl:if>
            </td>
          </xsl:otherwise>
        </xsl:choose>
      </tr>
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
          <xsl:when test="./Alias/@Context">
            <xsl:for-each select="./Alias/@Context">
              <xsl:choose>
                <xsl:when test="contains(./@Name, 'Note')">
                  <xsl:value-of select="substring-after('Note:',@Name)" />
                  <xsl:value-of select="':#ffffff !important;'" />
                </xsl:when>
                <xsl:when test="position() = 5">
                  <xsl:value-of select="substring-before(@Name,':')" />
                  <xsl:value-of select="':#0053ad !important;'" />
                </xsl:when>
                <xsl:when test="position() = 4">
                  <xsl:value-of select="substring-before(@Name,':')" />
                  <xsl:value-of select="':#ffbf9c !important;'" />
                </xsl:when>
                <xsl:when test="position() = 3">
                  <xsl:value-of select="substring-before(@Name,':')" />
                  <xsl:value-of select="':#96ff96 !important;'" />
                </xsl:when>
                <xsl:when test="position() = 2">
                  <xsl:value-of select="substring-before(@Name,':')" />
                  <xsl:value-of select="':#ffff96 !important;'" />
                </xsl:when>
                <xsl:when test="position() = 1">
                  <xsl:value-of select="substring-before(@Name,':')" />
                  <xsl:value-of select="':#bfffff !important;'" />
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="substring-before(@Name,':')" />
                  <xsl:value-of select="':#96ff96 !important;'" />
                </xsl:otherwise>
              </xsl:choose>
            </xsl:for-each>
          </xsl:when>
        </xsl:choose>
      </xsl:variable>
      <tr style="background: #193074 !important; color: #ffffff;">
        <th colspan="3" style="text-align: left;">
          <h4>
            <xsl:value-of disable-output-escaping="yes" select="@Name" />
            <xsl:if test="//FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@Mandatory = 'Yes'">
              <em>&#160;*&#160;</em>
            </xsl:if>
          </h4>
          <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
          <div class="oidinfo oid collapse d-print-none">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />]</div>
          <xsl:comment>&lt;![endif]</xsl:comment>
        <!-- <div class="oidinfo oid collapse">
          [OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />]
        </div> -->
      </th>
      <th colspan="2" style="text-align: right;">
        <xsl:for-each select="./Alias[@Context = 'IgType']">
          <xsl:value-of disable-output-escaping="yes" select="@Name" />
        </xsl:for-each>
        <xsl:if test="./@Domain">
          <h4>
            <xsl:call-template name="IGsplitter">
              <xsl:with-param name="aliasContext" select="'Sdtm'" />
              <xsl:with-param name="remaining-string" select="./@Domain" />
              <xsl:with-param name="pattern" select="'|'" />
              <xsl:with-param name="domainbgcolor" select="$domainBg" />
            </xsl:call-template>
          </h4>
        </xsl:if>
        <xsl:if test="./Alias/@Context = 'Sdtm'">
          <h5>
            <xsl:for-each select="./Alias[@Context = 'Sdtm']">
              <xsl:call-template name="splitter">
                <xsl:with-param name="aliasContext" select="'Sdtm'" />
                <xsl:with-param name="remaining-string" select="./@Name" />
                <xsl:with-param name="pattern" select="'|'" />
                <xsl:with-param name="domainbgcolor" select="$domainBg" />
              </xsl:call-template>
            </xsl:for-each>
          </h5>
        </xsl:if>
      </th>
    </tr>
    <tr>
      <td>
        <xsl:for-each select="ItemRef">
          <xsl:sort select="@OrderNumber" data-type="number" />
          <xsl:apply-templates select="//ItemDef[@OID = current()/@ItemOID]">
            <xsl:with-param name="domainBckg" select="$domainBg" />
          </xsl:apply-templates>
        </xsl:for-each>
      </td>
    </tr>
    <tr>
      <td>
        &#160;
      </td>
    </tr>
  </xsl:template>

  <xsl:template match="FormDef">
    <thead>
      <tr style="repeat-on-each-page padding: 2px;">
        <td colspan="5" style="background: #ffffff;">
          <h2>
            <xsl:value-of select="@Name" />
          </h2>
          <xsl:comment>[if !mso]&gt;&lt;!</xsl:comment>
          <div class="oidinfo oid collapse d-print-none">[OID=<xsl:value-of select="@OID" />, Version=<xsl:value-of select="@osb:version" />]</div>
          <xsl:comment>&lt;![endif]</xsl:comment>
        </td>
      </tr>
    </thead>
    <xsl:choose>
      <xsl:when test="./osb:DesignNotes">
        <tr>
          <td colspan="5" style="border: 1px solid #ccc; background: #BDD6EE; color: #000000;">
            <h4>
              Design Notes
            </h4>
          </td>
        </tr>
        <tr>
          <td colspan="5" style="border: 1px solid #ccc; padding: 2px; background: #ffffff;">
            <xsl:value-of disable-output-escaping="yes" select="./osb:DesignNotes" />
          </td>
        </tr>
      </xsl:when>
    </xsl:choose>
    <tr style="background-color:#ECECEC;">
      <td colspan="4" style="border: 1px solid #fff; padding: 2px;">
        Study ID: NNXXXX-XXXX
      </td>
      <td style="border: 1px solid #fff; padding: 2px;">
        Integration
      </td>
    </tr>
    <xsl:for-each select="ItemGroupRef">
      <xsl:sort select="current()/@OrderNumber" data-type="number" />
      <xsl:apply-templates
        select="//ItemGroupDef[@OID = current()/@ItemGroupOID]" />
      </xsl:for-each>
      <tr style="background-color:#ffffff;">
        <td colspan="5" style="border: 1px solid #fff; padding: 2px;">
          <xsl:for-each select="./Alias[@Context = 'Oracle']">
            <xsl:value-of disable-output-escaping="yes" select="@Name" />
          </xsl:for-each>
        </td>
      </tr>
    </xsl:template>

    <xsl:template match="Question">
      <xsl:param name="lockItem" />
      <xsl:param name="sdvItem" />
      <xsl:param name="mandatoryItem" />
      <xsl:value-of
        select="TranslatedText" />&#160; <xsl:choose>
        <xsl:when test="($lockItem = 'Yes') and ($sdvItem = 'Yes')">
          <span class="material-symbols-outlined">lock</span>&#160;<span
          class="material-symbols-outlined">account_tree</span>
        </xsl:when>
        <xsl:when test="$lockItem = 'Yes'">
          <span class="material-symbols-outlined">lock</span>
        </xsl:when>
        <xsl:when test="$sdvItem = 'Yes'">
          <span class="material-symbols-outlined">account_tree</span>
        </xsl:when>
        <xsl:otherwise> </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <xsl:template match="Decode">
      <xsl:value-of select="TranslatedText" />
    </xsl:template>

    <xsl:template name="Alias">
      <xsl:param name="aliasContext" />
      <xsl:param name="aliasName" />
      <xsl:param name="aliasBgcolor" />
      <div class="{$aliasContext} collapse">
        <div class="badge" style="background-color:{$aliasBgcolor} !important; border: 1px solid #000; color: white !important;">
          <xsl:value-of disable-output-escaping="yes" select="$aliasName" />
        </div>
      </div>
    </xsl:template>

    <xsl:template name="VendorExtensionActIns">
      <xsl:param name="vendorExtensionContext" />
      <xsl:param name="vendorExtensionName" />
      <xsl:variable name="activityInstanceBgcolor">
        <xsl:choose>
          <xsl:when test="./@osb:isDerived">
            <xsl:value-of select="'#339966'" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="'#b300008f'" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <div class="ActivityInstance collapse">
        <div class="badge-container" style="background-color:{$activityInstanceBgcolor} !important; border: 1px solid #000; color: white !important; padding: 10px; position: relative; border-radius: 8px;">

          <!-- Activity Instance Titre -->
          <div style="margin-bottom: 8px; font-weight: bold;">
           <u>Activity Instance</u>&#160;<xsl:value-of disable-output-escaping="yes" select="$vendorExtensionName" />
         </div>

         <!-- Container for the two sub-cartridges -->
         <div style="display: flex; gap: 8px;">
          <!-- Topic Code -->
          <div class="sub-badge" style="background-color: #b300008f !important; border: 1px solid #000; color: white; padding: 4px 8px; font-size: 0.85em; border-radius: 5px;">
            Topic Code: <xsl:value-of select="./@osb:topicCode" />
          </div>

          <!-- Adam Code -->
          <div class="sub-badge" style="background-color: #808080 !important; border: 1px solid #000; color: white; padding: 4px 8px; font-size: 0.85em; border-radius: 5px;">
            Param Code: <xsl:value-of select="./@osb:adamCode" />
          </div>
        </div>
      </div>
    </div>
  </xsl:template>

  <xsl:template name="IGsplitter">
    <xsl:param name="aliasContext" />
    <xsl:param name="remaining-string" />
    <xsl:param name="pattern" />
    <xsl:param name="domainbgcolor" />
    <xsl:variable name="itemBg">
      <xsl:choose>
        <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
          <xsl:value-of select="substring-after($domainbgcolor,':')" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'#bfffff !important;'" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <div class="{$aliasContext} collapse">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,$pattern)">
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note:')">
                <span class="badge-ig" style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string,$pattern)" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge-ig" style="border: 1px solid #000; color:black; background-color:{$itemBg} !important!">
                  <xsl:value-of select="normalize-space(concat(substring-before(substring-before($remaining-string,$pattern),':'),' (', substring-after(substring-before($remaining-string,$pattern),':'),')'))" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
          <xsl:call-template name="IGsplitter">
            <xsl:with-param name="aliasContext" select="$aliasContext" />
            <xsl:with-param name="remaining-string" select="substring-after($remaining-string,$pattern)" />
            <xsl:with-param name="pattern" select="$pattern" />
            <xsl:with-param name="domainbgcolor" select="$itemBg" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note:')">
                <span class="badge-ig" style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string)" />
                </span>
              </xsl:when>
              <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                <span class="badge-ig" style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string)" />
                </span>
              </xsl:when>
              <xsl:when test="$remaining-string != ''">
                <span class="badge-ig" style="border: 1px solid #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space(concat(substring-before($remaining-string,':'),' (', substring-after($remaining-string,':'),')'))" />
                </span>
              </xsl:when>
              <xsl:otherwise> </xsl:otherwise>
            </xsl:choose>
          </split-item>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template name="splitter">
    <xsl:param name="aliasContext" />
    <xsl:param name="remaining-string" />
    <xsl:param name="pattern" />
    <xsl:param name="domainbgcolor" />
    <xsl:variable name="domain-prefix" select="substring-before(concat($remaining-string, ':'), ':')" />

    <xsl:variable name="itemBg">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,'Note')">
          <xsl:value-of select="'#ffffff !important;'" />
        </xsl:when>
        <xsl:when test="string-length($domainbgcolor) = 7 and starts-with($domainbgcolor, '#')">
          <xsl:value-of select="$domainbgcolor" />
        </xsl:when>
        <xsl:when test="contains($domainbgcolor, concat($domain-prefix, ':'))">
          <xsl:variable name="domain-color-pair" select="substring-after(concat($domainbgcolor, '|'), concat($domain-prefix, ':'))" />
          <xsl:value-of select="substring-before($domain-color-pair, ' !important;|')" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'#ffbfaa !important;'" />
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
    <div class="{$aliasContext} collapse text-left">
      <xsl:choose>
        <xsl:when test="contains($remainingstrg,$pattern)">
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note')">
                <span class="badge" style="border: 1px dotted #000; color:black; background-color:{$itemBg} !important; border-radius: 5px;">
                  <xsl:value-of select="normalize-space(substring-before($remainingstrg,$pattern))" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge" style="border: 1px solid #000; color:black; background-color:{$itemBg}! important; border-radius: 5px;">
                  <xsl:value-of select="normalize-space(substring-before($remainingstrg,$pattern))" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
          <xsl:call-template name="splitter">
            <xsl:with-param name="aliasContext" select="$aliasContext" />
            <xsl:with-param name="remaining-string" select="substring-after($remainingstrg,$pattern)" />
            <xsl:with-param name="pattern" select="$pattern" />
            <xsl:with-param name="domainbgcolor" select="$domainbgcolor" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note')">
                <span class="badge" style="border: 1px dotted #000; color:black; background-color:{$itemBg} !important; border-radius: 5px;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:when>
              <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                <span class="badge" style="border: 1px dotted #000; color:black; background-color:#ffffff !important; border-radius: 5px;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge" style="border: 1px solid #000; color:black; background-color:{$itemBg} !important; border-radius: 5px;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

</xsl:stylesheet>