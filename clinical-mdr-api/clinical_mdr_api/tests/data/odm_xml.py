# pylint: disable=too-many-lines, line-too-long
export_study_event = """<?xml version="1.0" encoding="utf-8"?>
                <ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
                xmlns:osb="url2" xmlns:prefix="url1" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
                    <Study OID="name1-odm_study_event1">
                        <GlobalVariables>
                            <ProtocolName>name1</ProtocolName>
                            <StudyName>name1</StudyName>
                            <StudyDescription>name1</StudyDescription>
                        </GlobalVariables>
                        <BasicDefinitions>
                            <MeasurementUnit OID="unit_definition_root1" Name="name1" osb:version="0.1">
                                <Symbol>
                                    <TranslatedText xml:lang="en">name1</TranslatedText>
                                </Symbol>
                            </MeasurementUnit>
                        </BasicDefinitions>
                        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                            <FormDef OID="oid1" Name="name1" Repeating="Yes" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <ItemGroupRef ItemGroupOID="oid1" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="oid2" prefix:nameThree="No" />
                                <prefix:nameOne>test value</prefix:nameOne>
                            </FormDef>
                            <ItemGroupDef OID="oid1" Name="name1" Repeating="No" Purpose="purpose1" SASDatasetName="sas_dataset_name1" Domain="code_submission_value1:preferred_term1|code_submission_value2:preferred_term2" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                                <osb:DomainColor>code_submission_value1:#bfffff !important;</osb:DomainColor>
                                <osb:DomainColor>code_submission_value2:#ffff96 !important;</osb:DomainColor>
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <ItemRef ItemOID="oid1" Mandatory="Yes" OrderNumber="1" MethodOID="oid1" CollectionExceptionConditionOID="oid1" prefix:nameThree="No" />
                            </ItemGroupDef>
                            <ItemDef OID="oid1" Name="name1" Origin="origin1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1" SDSVarName="sdsvarname1" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                                <Question>
                                    <TranslatedText xml:lang="en" osb:version="1.0">name1</TranslatedText>
                                </Question>
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <CodeListRef CodeListOID="submission_value1@oid1" />
                                <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                            </ItemDef>
                            <ConditionDef OID="oid1" Name="name1" osb:version="1.0">
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
                            </ConditionDef>
                            <ConditionDef OID="oid2" Name="name2" osb:version="1.0">
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
                            </ConditionDef>
                            <MethodDef OID="oid1" Name="name1" Type="type1" osb:version="1.0">
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
                            </MethodDef>
                            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1" osb:version="1.0">
                                <CodeListItem CodedValue="code_submission_value1" OrderNumber="1" osb:mandatory="False" osb:name="name1" osb:OID="term1" osb:version="1.0">
                                    <Decode>
                                        <TranslatedText xml:lang="en">custom text</TranslatedText>
                                    </Decode>
                                </CodeListItem>
                            </CodeList>
                        </MetaDataVersion>
                    </Study>
                </ODM>"""
export_form = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="url2" xmlns:prefix="url1" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
    <Study OID="name1-odm_form1">
        <GlobalVariables>
            <ProtocolName>name1</ProtocolName>
            <StudyName>name1</StudyName>
            <StudyDescription>name1</StudyDescription>
        </GlobalVariables>
        <BasicDefinitions>
            <MeasurementUnit OID="unit_definition_root1" Name="name1" osb:version="0.1">
                <Symbol>
                    <TranslatedText xml:lang="en">name1</TranslatedText>
                </Symbol>
            </MeasurementUnit>
        </BasicDefinitions>
        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
            <FormDef OID="oid1" Name="name1" Repeating="Yes" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <ItemGroupRef ItemGroupOID="oid1" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="oid2" prefix:nameThree="No" />
                <prefix:nameOne>test value</prefix:nameOne>
            </FormDef>
            <ItemGroupDef OID="oid1" Name="name1" Repeating="No" Purpose="purpose1" SASDatasetName="sas_dataset_name1" Domain="code_submission_value1:preferred_term1|code_submission_value2:preferred_term2" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                <osb:DomainColor>code_submission_value1:#bfffff !important;</osb:DomainColor>
                <osb:DomainColor>code_submission_value2:#ffff96 !important;</osb:DomainColor>
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <ItemRef ItemOID="oid1" Mandatory="Yes" OrderNumber="1" MethodOID="oid1" CollectionExceptionConditionOID="oid1" prefix:nameThree="No" />
            </ItemGroupDef>
            <ItemDef OID="oid1" Name="name1" Origin="origin1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1" SDSVarName="sdsvarname1" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                <Question>
                    <TranslatedText xml:lang="en" osb:version="1.0">name1</TranslatedText>
                </Question>
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <CodeListRef CodeListOID="submission_value1@oid1" />
                <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
            </ItemDef>
            <ConditionDef OID="oid1" Name="name1" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </ConditionDef>
            <ConditionDef OID="oid2" Name="name2" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </ConditionDef>
            <MethodDef OID="oid1" Name="name1" Type="type1" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </MethodDef>            
            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1" osb:version="1.0">
                <CodeListItem CodedValue="code_submission_value1" OrderNumber="1" osb:mandatory="False" osb:name="name1" osb:OID="term1" osb:version="1.0">
                    <Decode>
                        <TranslatedText xml:lang="en">custom text</TranslatedText>
                    </Decode>
                </CodeListItem>
            </CodeList>
        </MetaDataVersion>
    </Study>
</ODM>"""
export_item_group = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="url2" xmlns:prefix="url1" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
    <Study OID="name1-odm_item_group1">
        <GlobalVariables>
            <ProtocolName>name1</ProtocolName>
            <StudyName>name1</StudyName>
            <StudyDescription>name1</StudyDescription>
        </GlobalVariables>
        <BasicDefinitions>
            <MeasurementUnit OID="unit_definition_root1" Name="name1" osb:version="0.1">
                <Symbol>
                    <TranslatedText xml:lang="en">name1</TranslatedText>
                </Symbol>
            </MeasurementUnit>
        </BasicDefinitions>
        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
            <ItemGroupDef OID="oid1" Name="name1" Repeating="No" Purpose="purpose1" SASDatasetName="sas_dataset_name1" Domain="code_submission_value1:preferred_term1|code_submission_value2:preferred_term2" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                <osb:DomainColor>code_submission_value1:#bfffff !important;</osb:DomainColor>
                <osb:DomainColor>code_submission_value2:#ffff96 !important;</osb:DomainColor>
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <ItemRef ItemOID="oid1" Mandatory="Yes" OrderNumber="1" MethodOID="oid1" CollectionExceptionConditionOID="oid1" prefix:nameThree="No" />
            </ItemGroupDef>
            <ItemDef OID="oid1" Name="name1" Origin="origin1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1" SDSVarName="sdsvarname1" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                <Question>
                    <TranslatedText xml:lang="en" osb:version="1.0">name1</TranslatedText>
                </Question>
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <CodeListRef CodeListOID="submission_value1@oid1" />
                <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
            </ItemDef>
            <ConditionDef OID="oid1" Name="name1" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </ConditionDef>
            <MethodDef OID="oid1" Name="name1" Type="type1" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </MethodDef>
            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1" osb:version="1.0">
                <CodeListItem CodedValue="code_submission_value1" OrderNumber="1" osb:mandatory="False" osb:name="name1" osb:OID="term1" osb:version="1.0">
                    <Decode>
                        <TranslatedText xml:lang="en">custom text</TranslatedText>
                    </Decode>
                </CodeListItem>
            </CodeList>
        </MetaDataVersion>
    </Study>
</ODM>"""
export_item = """<?xml version="1.0" encoding="utf-8"?>
                <ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="url2" xmlns:prefix="url1" ODMVersion="1.3.2"
                FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
                    <Study OID="name1-odm_item1">
                        <GlobalVariables>
                            <ProtocolName>name1</ProtocolName>
                            <StudyName>name1</StudyName>
                            <StudyDescription>name1</StudyDescription>
                        </GlobalVariables>
                        <BasicDefinitions>
                            <MeasurementUnit OID="unit_definition_root1" Name="name1" osb:version="0.1">
                                <Symbol>
                                    <TranslatedText xml:lang="en">name1</TranslatedText>
                                </Symbol>
                            </MeasurementUnit>
                        </BasicDefinitions>
                        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                            <ItemDef OID="oid1" Name="name1" Origin="origin1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1"
                            SDSVarName="sdsvarname1" osb:version="1.0" osb:instruction="instruction1" osb:sponsorInstruction="sponsor_instruction1">
                                <Question>
                                    <TranslatedText xml:lang="en" osb:version="1.0">name1</TranslatedText>
                                </Question>
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <CodeListRef CodeListOID="submission_value1@oid1" />
                                <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                            </ItemDef>
                            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1" osb:version="1.0">
                                <CodeListItem CodedValue="code_submission_value1" OrderNumber="1" osb:mandatory="False" osb:name="name1" osb:OID="term1" osb:version="1.0">
                                    <Decode>
                                        <TranslatedText xml:lang="en">custom text</TranslatedText>
                                    </Decode>
                                </CodeListItem>
                            </CodeList>
                        </MetaDataVersion>
                    </Study>
                </ODM>"""
export_with_csv = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="url2" xmlns:prefix="url1" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
    <Study OID="name1-odm_study_event1">
        <GlobalVariables>
            <ProtocolName>name1</ProtocolName>
            <StudyName>name1</StudyName>
            <StudyDescription>name1</StudyDescription>
        </GlobalVariables>
        <BasicDefinitions>
            <MeasurementUnit OID="unit_definition_root1" Name="name1" osb:version="0.1">
                <Symbol>
                    <TranslatedText xml:lang="en">name1</TranslatedText>
                </Symbol>
            </MeasurementUnit>
        </BasicDefinitions>
        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
            <FormDef OID="oid1" Name="name1" Repeating="Yes" CompletionInstructions="instruction1" ImplementationNotes="sponsor_instruction1" ov="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <osb:ItemGroupRef ItemGroupOID="oid1" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="oid2" prefix:nameThree="No" />
                <prefix:nameOne>test value</prefix:nameOne>
                <Alias Name="instruction1" Context="CompletionInstructions" />
                <Alias Name="sponsor_instruction1" Context="ImplementationNotes" />
            </FormDef>
            <ItemGroupDef OID="oid1" Name="name1" Repeating="No" Purpose="purpose1" SASDatasetName="sas_dataset_name1" Domain="code_submission_value1:preferred_term1|code_submission_value2:preferred_term2" osb:version="1.0" CompletionInstructions="instruction1" ImplementationNotes="sponsor_instruction1">
                <DomainColor>code_submission_value1:#bfffff !important;</DomainColor>
                <DomainColor>code_submission_value2:#ffff96 !important;</DomainColor>
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <osb:ItemRef ItemOID="oid1" Mandatory="Yes" OrderNumber="1" MethodOID="oid1" CollectionExceptionConditionOID="oid1" prefix:nameThree="No" />
                <Alias Name="instruction1" Context="CompletionInstructions" />
                <Alias Name="sponsor_instruction1" Context="ImplementationNotes" />
            </ItemGroupDef>
            <ItemDef OID="oid1" Name="name1" Origin="origin1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1" SDSVarName="sdsvarname1" osb:version="1.0" CompletionInstructions="instruction1" ImplementationNotes="sponsor_instruction1">
                <Question>
                    <TranslatedText xml:lang="en" osb:version="1.0">name1</TranslatedText>
                </Question>
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" osb:version="0.1" />
                <CodeListRef CodeListOID="submission_value1@oid1" />
                <osb:measurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                <Alias Name="instruction1" Context="CompletionInstructions" />
                <Alias Name="sponsor_instruction1" Context="ImplementationNotes" />
            </ItemDef>
            <ConditionDef OID="oid1" Name="name1" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </ConditionDef>
            <ConditionDef OID="oid2" Name="name2" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </ConditionDef>
            <MethodDef OID="oid1" Name="name1" Type="type1" osb:version="1.0">
                <Description>
                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
            </MethodDef>
            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1" osb:version="1.0">
                <CodeListItem CodedValue="code_submission_value1" OrderNumber="1" osb:mandatory="False" osb:name="name1" osb:OID="term1" osb:version="1.0">
                    <Decode>
                        <TranslatedText xml:lang="en">custom text</TranslatedText>
                    </Decode>
                </CodeListItem>
            </CodeList>
        </MetaDataVersion>
    </Study>
</ODM>"""
export_with_namespace = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:prefix="url1" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
    <Study OID="name1-odm_study_event1">
        <GlobalVariables>
            <ProtocolName>name1</ProtocolName>
            <StudyName>name1</StudyName>
            <StudyDescription>name1</StudyDescription>
        </GlobalVariables>
        <BasicDefinitions>
            <MeasurementUnit OID="unit_definition_root1" Name="name1">
                <Symbol>
                    <TranslatedText xml:lang="en">name1</TranslatedText>
                </Symbol>
            </MeasurementUnit>
        </BasicDefinitions>
        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
            <FormDef OID="oid1" Name="name1" Repeating="Yes">
                <Description>
                    <TranslatedText xml:lang="en">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" />
                <ItemGroupRef ItemGroupOID="oid1" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="oid2" prefix:nameThree="No" />
                <prefix:nameOne>test value</prefix:nameOne>
            </FormDef>
            <ItemGroupDef OID="oid1" Name="name1" Repeating="No" Purpose="purpose1" SASDatasetName="sas_dataset_name1" Domain="code_submission_value1:preferred_term1|code_submission_value2:preferred_term2">
                <Description>
                    <TranslatedText xml:lang="en">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" />
                <ItemRef ItemOID="oid1" Mandatory="Yes" OrderNumber="1" MethodOID="oid1" CollectionExceptionConditionOID="oid1" prefix:nameThree="No" />
            </ItemGroupDef>
            <ItemDef OID="oid1" Name="name1" Origin="origin1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1" SDSVarName="sdsvarname1">
                <Question>
                    <TranslatedText xml:lang="en">name1</TranslatedText>
                </Question>
                <Description>
                    <TranslatedText xml:lang="en">description1</TranslatedText>
                </Description>
                <Alias Name="name1" Context="context1" />
                <CodeListRef CodeListOID="submission_value1@oid1" />
                <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
            </ItemDef>
            <ConditionDef OID="oid1" Name="name1">
                <Description>
                    <TranslatedText xml:lang="en">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1">expression1</FormalExpression>
            </ConditionDef>
            <ConditionDef OID="oid2" Name="name2">
                <Description>
                    <TranslatedText xml:lang="en">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1">expression1</FormalExpression>
            </ConditionDef>
            <MethodDef OID="oid1" Name="name1" Type="type1">
                <Description>
                    <TranslatedText xml:lang="en">description1</TranslatedText>
                </Description>
                <FormalExpression Context="context1">expression1</FormalExpression>
            </MethodDef>
            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1">
                <CodeListItem CodedValue="code_submission_value1" OrderNumber="1">
                    <Decode>
                        <TranslatedText xml:lang="en">custom text</TranslatedText>
                    </Decode>
                </CodeListItem>
            </CodeList>
        </MetaDataVersion>
    </Study>
</ODM>"""


import_input1 = """<?xml version="1.0" encoding="utf-8"?>
        <?xml-stylesheet type="text/xsl" href="odm_study_event_sdtmcrf.xsl"?>
        <ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1666353293513" CreationDateTime="2022-10-21 13:54:53.513447" Granularity="All" xmlns:osb="url2" xmlns:clinspark="https://www.clinspark.com">
            <Study OID="ODM version 1.3.2 with DoB-T.ODM-1-3-2-V1">
                <GlobalVariables>
                    <ProtocolName>ODM version 1.3.2 with DoB</ProtocolName>
                    <StudyName>ODM version 1.3.2 with DoB</StudyName>
                    <StudyDescription>ODM version 1.3.2 with DoB</StudyDescription>
                </GlobalVariables>
                <BasicDefinitions>
                    <MeasurementUnit OID="unit_definition_root1" Name="name1">
                        <Symbol>
                            <TranslatedText xml:lang="en">name1</TranslatedText>
                        </Symbol>
                    </MeasurementUnit>
                </BasicDefinitions>
                <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                    <FormDef OID="F.DM" Name="Informed Consent and Demography" Repeating="No" osb:version="1.0" osb:instruction="form instruction" osb:sponsorInstruction="form sponsor instruction" osb:allows="uds">
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent and Demography form</TranslatedText>
                        </Description>
                        <Alias Name="name1" Context="context1" />
                        <ItemGroupRef ItemGroupOID="G.DM.IC" Mandatory="Yes" OrderNumber="1" osb:locked="Yes" clinspark:connectivity="Yes" />
                        <ItemGroupRef ItemGroupOID="G.DM.DM" Mandatory="Yes" OrderNumber="2" osb:locked="No" clinspark:connectivity="Yes" />
                    </FormDef>
                    <FormDef OID="F.VS" Name="Vital Signs" Repeating="No" osb:version="1.0" osb:instruction="form instruction" osb:sponsorInstruction="form sponsor instruction" osb:allows="second">
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Vital signs form</TranslatedText>
                        </Description>
                        <Alias Name="name1" Context="context1" />
                        <ItemGroupRef ItemGroupOID="G.VS.VS" Mandatory="Yes" OrderNumber="1" osb:locked="Yes" />
                        <ItemGroupRef ItemGroupOID="G.VS.BPP" Mandatory="Yes" OrderNumber="2" osb:locked="Yes" />
                    </FormDef>
                    <ItemGroupDef OID="G.VS.BPP" Name="Blood pressure and pulse" Repeating="No" Purpose="Tabulation" SASDatasetName="VITALSIGNSBPP" Domain="VS:Vital Signs Domain" osb:version="1.0" osb:instruction="item group instruction" osb:sponsorInstruction="item group sponsor instruction" osb:gr="ig1">
                        <osb:DomainColor>VS:#bfffff !important;</osb:DomainColor>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Blood pressure and pulse</TranslatedText>
                        </Description>
                        <ItemRef ItemOID="I.SYSBP" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="C.OID1" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.DIABP" Mandatory="Yes" OrderNumber="2" osb:sdv="Yes" osb:dataEntryRequired="Yes" />
                        <ItemRef ItemOID="I.POSITION" Mandatory="Yes" OrderNumber="3" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.LATERALITY" Mandatory="Yes" OrderNumber="4" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.LOC" Mandatory="Yes" OrderNumber="5" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.PULSE" Mandatory="Yes" OrderNumber="6" osb:sdv="Yes" />
                        <Alias Name="name1" Context="context1" />
                    </ItemGroupDef>
                    <ItemGroupDef OID="G.DM.DM" Name="General Demography" Repeating="No" Purpose="Tabulation" SASDatasetName="DEMOG" Domain="DM:Demographics Domain" osb:version="1.0" osb:instruction="item group instruction" osb:sponsorInstruction="item group sponsor instruction" osb:gr="ig2">
                        <osb:DomainColor>DM:#bfffff !important;</osb:DomainColor>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">General Demographic item group</TranslatedText>
                        </Description>
                        <ItemRef ItemOID="I.BRTHDTCARGUS" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="C.OID2" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.BRTHDTC" Mandatory="Yes" OrderNumber="2" osb:sdv="Yes" MethodOID="M.OID1" />
                        <ItemRef ItemOID="I.AGE" Mandatory="Yes" OrderNumber="3" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.SEX" Mandatory="Yes" OrderNumber="4" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.SEXDEA" Mandatory="Yes" OrderNumber="5" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.ETHNIC" Mandatory="Yes" OrderNumber="6" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RACE" Mandatory="Yes" OrderNumber="7" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RACEOTH" Mandatory="Yes" OrderNumber="8" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.SUBJID" Mandatory="Yes" OrderNumber="9" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.PREVSUBJ" Mandatory="Yes" OrderNumber="10" osb:sdv="Yes" />
                        <Alias Name="name2" Context="context2" />
                    </ItemGroupDef>
                    <ItemGroupDef OID="G.DM.IC" Name="Informed Consent" Repeating="No" Purpose="Tabulation" SASDatasetName="DEMOG" Domain="DM:Demographics Domain" osb:version="1.0" osb:instruction="item group instruction" osb:sponsorInstruction="item group sponsor instruction" osb:gr="ig3">
                        <osb:DomainColor>DM:#bfffff !important;</osb:DomainColor>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent item group</TranslatedText>
                        </Description>
                        <ItemRef ItemOID="I.STUDYID" Mandatory="Yes" OrderNumber="1" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RFICDAT" Mandatory="Yes" OrderNumber="2" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RFICTIM" Mandatory="Yes" OrderNumber="3" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RFICDATLAR1" Mandatory="Yes" OrderNumber="4" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RFICTIMLAR1" Mandatory="Yes" OrderNumber="5" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RFICDATLAR2" Mandatory="Yes" OrderNumber="6" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.RFICTIMLAR2" Mandatory="Yes" OrderNumber="7" osb:sdv="Yes" />
                    </ItemGroupDef>
                    <ItemGroupDef OID="G.VS.VS" Name="Vital Signs" Repeating="Yes" Purpose="Tabulation" SASDatasetName="VITALSIGNS" Domain="VS:Vital Signs Domain" osb:version="1.0" osb:instruction="item group instruction" osb:sponsorInstruction="item group sponsor instruction" osb:gr="ig4">
                        <osb:DomainColor>VS:#bfffff !important;</osb:DomainColor>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Vital signs</TranslatedText>
                        </Description>
                        <ItemRef ItemOID="I.STUDYID" Mandatory="Yes" OrderNumber="1" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.SUBJID" Mandatory="Yes" OrderNumber="2" osb:sdv="Yes" />
                        <ItemRef ItemOID="I.VSDAT" Mandatory="Yes" OrderNumber="3" osb:sdv="Yes" />
                    </ItemGroupDef>
                    <ItemDef OID="I.AGE" Name="Age" Origin="Collected Value" DataType="integer" Length="3" SASFieldName="AGE" SDSVarName="AGE" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction" osb:allowsMultiChoice="true">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Age</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Age</TranslatedText>
                        </Description>
                        <CodeListRef CodeListOID="codelist submission value1@I.AGE" />
                        <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                        <osb:Sometag osb:someAttr="a value" osb:version="1.0">inner text</osb:Sometag>
                    </ItemDef>
                    <ItemDef OID="I.LOC" Name="Anatomical Location" Origin="Collected Value" DataType="string" Length="15" SASFieldName="LOCATION" SDSVarName="VSLOC where VSTESTCD=SYSBP | VSLOC where VSTESTCD=DIABP" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction" osb:allowsMultiChoice="false">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Anatomical Location</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Anatomical Location of the measurement</TranslatedText>
                        </Description>
                        <osb:Sometag osb:someAttr="a value" osb:version="1.0">inner text</osb:Sometag>
                    </ItemDef>
                    <ItemDef OID="I.RFICDAT" Name="Date informed consent obtained" Origin="Collected Value" DataType="date" Length="10" SASFieldName="RFICDAT" SDSVarName="RFICDTC, DSSTDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date informed consent obtained</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent DATE</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.RFICDATLAR2" Name="Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated]" Origin="Collected Value" DataType="date" Length="10" SASFieldName="RFICDAT" SDSVarName="RFICDTC, DSSTDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent DATE (Legal or authorised representative 2)</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.RFICDATLAR1" Name="Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) [de-activated]" Origin="Collected Value" DataType="date" Length="10" SASFieldName="RFICDAT" SDSVarName="RFICDTC, DSSTDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) [de-activated ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent Date (Legal or authorised representative 1)</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.BRTHDTC" Name="Date of birth" Origin="Collected Value" DataType="date" Length="10" SASFieldName="BRTHDAT" SDSVarName="BRTHDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date of birth</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date of birth</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.BRTHDTCARGUS" Name="Date of birth (only for Argus interface) [hidden]" Origin="Collected Value" DataType="date" Length="10" SASFieldName="BRTHDAT" SDSVarName="BRTHDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date of birth (only for Argus interface) [hidden ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date of birth (only for Argus interface) [hidden ]</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.VSDAT" Name="Date of examination" Origin="Collected Value" DataType="date" Length="10" SASFieldName="VSDAT" SDSVarName="VSDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date of examination</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Date of examination [de-activated ]</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.DIABP" Name="Diastolic blood pressure" Origin="Collected Value" DataType="integer" Length="3" SASFieldName="BP_DIASTOLIC" SDSVarName="VSORRES where VSTESTCD=DIABP, VSORRESU where VSTESTCD=DIABP" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Diastolic blood pressure</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Diastolic blood pressure</TranslatedText>
                        </Description>
                        <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                    </ItemDef>
                    <ItemDef OID="I.ETHNIC" Name="Ethnicity" Origin="Collected Value" DataType="string" Length="20" SASFieldName="ETHNIC" SDSVarName="ETHNIC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Ethnicity</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Ethinicity</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.RFICTIMLAR1" Name="Informed Consent TIME obtained by Parents/Legally Acceptable Representative (LAR) [de-activated]" Origin="Collected Value" DataType="time" Length="5" SASFieldName="RFICTIM" SDSVarName="RFICDTC, DSSTDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent TIME obtained by Parents/Legally Acceptable Representative (LAR) [de-activated ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent Time (Legal or authorised representative 1)</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.RFICTIMLAR2" Name="Informed Consent Time obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated]" Origin="Collected Value" DataType="time" Length="5" SASFieldName="RFICTIM" SDSVarName="RFICDTC, DSSTDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent Time obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent Time (Legal or authorised representative 2)</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.LATERALITY" Name="Laterality" Origin="Collected Value" DataType="string" Length="15" SASFieldName="LATERALITY" SDSVarName="VSLAT where VSTESTCD=SYSBP | VSLAT where VSTESTCD=DIABP" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Laterality</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Laterality of the measurement</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.POSITION" Name="Position" Origin="Collected Value" DataType="string" Length="15" SASFieldName="POSITION" SDSVarName="VSPOS where VSTESTCD=SYSBP | VSPOS where VSTESTCD=DIABP" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Position</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Position of the subject</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.PREVSUBJ" Name="Previous Subject No." Origin="Collected Value" DataType="string" Length="10" SASFieldName="PREVSUBJ" SDSVarName="PREVSUBJ" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Previous Subject No.</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Previous Subject No.</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.PULSE" Name="Pulse" Origin="Collected Value" DataType="integer" Length="3" SASFieldName="PULSE" SDSVarName="VSORRES/VSORRESU when VSTESTCD=PULSE" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Pulse</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Pulse</TranslatedText>
                        </Description>
                        <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                    </ItemDef>
                    <ItemDef OID="I.RACE" Name="Race" Origin="Collected Value" DataType="string" Length="40" SASFieldName="RACE" SDSVarName="RACE" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Race</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Race</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.RACEOTH" Name="Race other" Origin="Collected Value" DataType="string" Length="40" SASFieldName="RACEOTH" SDSVarName="RACEOTH in SUPPDM" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Race other</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Race other</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.SEXDEA" Name="Sex [de-activated]" Origin="Protocol Value" DataType="string" Length="15" SASFieldName="SEX" SDSVarName="SEX" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Sex [de-activated ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Sex [de-activated ]</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.SEX" Name="Sex [read-only]" Origin="Collected Value" DataType="string" Length="15" SASFieldName="SEX" SDSVarName="SEX" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Sex [read-only ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Sex [read-only ]</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.STUDYID" Name="Study ID" Origin="Protocol Value" DataType="string" Length="11" SASFieldName="STUDYID" SDSVarName="STUDYID" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Study ID</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Study Identifier</TranslatedText>
                        </Description>
                        <CodeListRef CodeListOID="codelist submission value1@I.STUDYID" />
                    </ItemDef>
                    <ItemDef OID="I.SUBJID" Name="Subject No. [read-only]" Origin="Collected Value" DataType="string" Length="10" SASFieldName="SUBJID" SDSVarName="SUBJID" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Subject No. [read-only ]</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Subject No.</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ItemDef OID="I.SYSBP" Name="Systolic blood pressure" Origin="Collected Value" DataType="integer" Length="3" SASFieldName="BP_SYSTOLIC" SDSVarName="VSORRES where VSTESTCD=SYSBP, VSORRESU where VSTESTCD=SYSBP" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Systolic blood pressure</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Systolic blood pressure</TranslatedText>
                        </Description>
                        <MeasurementUnitRef MeasurementUnitOID="unit_definition_root1" />
                    </ItemDef>
                    <ItemDef OID="I.RFICTIM" Name="Time informed consent obtained" Origin="Collected Value" DataType="time" Length="5" SASFieldName="RFICTIM" SDSVarName="RFICDTC, DSSTDTC" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Time informed consent obtained</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent time</TranslatedText>
                        </Description>
                    </ItemDef>
                    <ConditionDef OID="C.OID1" Name="Condition1">
                        <Description>
                            <TranslatedText xml:lang="en">Condition 1 Description</TranslatedText>
                        </Description>
                        <Question>
                            <TranslatedText xml:lang="en">Condition 1 Description Name</TranslatedText>
                        </Question>
                        <FormalExpression Context="XPath">Formal Expression 1</FormalExpression>
                    </ConditionDef>
                    <ConditionDef OID="C.OID2" Name="Condition2">
                        <Description>
                            <TranslatedText xml:lang="en">Condition 2 Description</TranslatedText>
                            <TranslatedText xml:lang="da">Condition 3 Description</TranslatedText>
                        </Description>
                        <Question>
                            <TranslatedText xml:lang="da">Condition 3 Description Name</TranslatedText>
                            <TranslatedText xml:lang="en">Condition 2 Description Name</TranslatedText>
                            <TranslatedText xml:lang="ar">Condition 4 Description Name</TranslatedText>
                        </Question>
                        <FormalExpression Context="XPath">Formal Expression 2</FormalExpression>
                    </ConditionDef>
                    <MethodDef OID="M.OID1" Name="Method1">
                        <Description>
                            <TranslatedText xml:lang="en">Method 1 Description</TranslatedText>
                            <TranslatedText xml:lang="da">Method 2 Description</TranslatedText>
                        </Description>
                        <Question>
                            <TranslatedText xml:lang="ar">Method 1 Description Name</TranslatedText>
                            <TranslatedText xml:lang="en">Method 2 Description Name</TranslatedText>
                            <TranslatedText xml:lang="da">Method 3 Description Name</TranslatedText>
                        </Question>
                        <FormalExpression Context="XPath">Formal Expression 1</FormalExpression>
                    </MethodDef>
                    <CodeList OID="codelist submission value1@I.STUDYID" Name="editable_cr" DataType="string" SASFormatName="codelist submission value1" osb:version="1.0">
                        <CodeListItem CodedValue="codeSubmissionValue" OrderNumber="2" osb:mandatory="True" osb:name="term_value_name1" osb:OID="term_root_final" osb:version="1.0">
                            <Decode>
                                <TranslatedText xml:lang="en">preferred_term</TranslatedText>
                            </Decode>
                        </CodeListItem>
                    </CodeList>
                    <CodeList OID="codelist submission value1@I.AGE" Name="editable_cr" DataType="string" SASFormatName="codelist submission value1" osb:version="1.0">
                        <CodeListItem CodedValue="codeSubmissionValue" OrderNumber="1" osb:mandatory="False" osb:name="term_value_name1" osb:OID="term_root_final" osb:version="1.0">
                            <Decode>
                                <TranslatedText xml:lang="en">preferred_term</TranslatedText>
                            </Decode>
                        </CodeListItem>
                    </CodeList>
                </MetaDataVersion>
            </Study>
        </ODM>"""
import_output1 = {
    "vendor_namespaces": [
        {
            "start_date": "2022-12-01T13:06:35.864543+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorNamespace_000001",
            "name": "CLINSPARK",
            "library_name": "Sponsor",
            "prefix": "clinspark",
            "url": "https://www.clinspark.com",
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000008",
                    "name": "connectivity",
                    "data_type": "string",
                    "compatible_types": ["ItemGroupRef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                }
            ],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:36.138481+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_namespace2",
            "name": "OSB",
            "library_name": "Sponsor",
            "prefix": "osb",
            "url": "url2",
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "Sometag",
                    "compatible_types": ["ItemDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "odm_vendor_element2",
                    "name": "nameTwo",
                    "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000006",
                    "name": "allows",
                    "data_type": "string",
                    "compatible_types": ["FormDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "allowsMultiChoice",
                    "data_type": "string",
                    "compatible_types": ["ItemDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000005",
                    "name": "dataEntryRequired",
                    "data_type": "string",
                    "compatible_types": ["ItemRef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "gr",
                    "data_type": "string",
                    "compatible_types": ["ItemGroupDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000007",
                    "name": "locked",
                    "data_type": "string",
                    "compatible_types": ["ItemGroupRef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000004",
                    "name": "sdv",
                    "data_type": "string",
                    "compatible_types": ["ItemRef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
            ],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "vendor_attributes": [
        {
            "start_date": "2022-12-01T13:06:51.550638+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000006",
            "name": "allows",
            "library_name": "Sponsor",
            "compatible_types": ["FormDef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:41.198850+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000001",
            "name": "allowsMultiChoice",
            "library_name": "Sponsor",
            "compatible_types": ["ItemDef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-08T07:29:45.187324+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000008",
            "name": "connectivity",
            "library_name": "Sponsor",
            "compatible_types": ["ItemGroupRef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "OdmVendorNamespace_000001",
                "name": "CLINSPARK",
                "prefix": "clinspark",
                "url": "https://www.clinspark.com",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:51.550638+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000005",
            "name": "dataEntryRequired",
            "library_name": "Sponsor",
            "compatible_types": ["ItemRef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:49.604103+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000003",
            "name": "gr",
            "library_name": "Sponsor",
            "compatible_types": ["ItemGroupDef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:51.550638+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000007",
            "name": "locked",
            "library_name": "Sponsor",
            "compatible_types": ["ItemGroupRef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:51.550638+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000004",
            "name": "sdv",
            "library_name": "Sponsor",
            "compatible_types": ["ItemRef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:42.197513+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000002",
            "name": "someAttr",
            "library_name": "Sponsor",
            "compatible_types": [],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": None,
            "vendor_element": {
                "uid": "OdmVendorElement_000001",
                "name": "Sometag",
                "compatible_types": ["ItemDef"],
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "vendor_elements": [
        {
            "start_date": "2022-12-01T13:06:41.819393+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorElement_000001",
            "name": "Sometag",
            "library_name": "Sponsor",
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000002",
                    "name": "someAttr",
                    "data_type": "string",
                    "compatible_types": [],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                }
            ],
            "compatible_types": ["ItemDef"],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-12T09:16:09.313000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_element2",
            "name": "nameTwo",
            "library_name": "Sponsor",
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_attributes": [],
            "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "study_events": [
        {
            "start_date": "2022-12-01T13:06:52.938606+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmStudyEvent_000001",
            "name": "ODM version 1.3.2 with DoB",
            "library_name": "Sponsor",
            "oid": "ODM version 1.3.2 with DoB",
            "effective_date": None,
            "retired_date": None,
            "description": None,
            "display_in_tree": True,
            "forms": [
                {
                    "uid": "OdmForm_000001",
                    "name": "Informed Consent and Demography",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
                {
                    "uid": "OdmForm_000002",
                    "name": "Vital Signs",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
            ],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
    "forms": [
        {
            "start_date": "2022-12-01T13:06:52.254571+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000001",
            "name": "Informed Consent and Demography",
            "library_name": "Sponsor",
            "oid": "F.DM",
            "repeating": "No",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000036",
                    "name": "Informed Consent and Demography form",
                    "language": "ENG",
                    "description": "Informed Consent and Demography form",
                    "instruction": "form instruction",
                    "sponsor_instruction": "form sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [
                {
                    "uid": "OdmAlias_000001",
                    "context": "context1",
                    "name": "name1",
                    "version": "1.0",
                }
            ],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000003",
                    "oid": "G.DM.IC",
                    "name": "Informed Consent",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000007",
                                "name": "locked",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                            {
                                "uid": "OdmVendorAttribute_000008",
                                "name": "connectivity",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "OdmVendorNamespace_000001",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItemGroup_000002",
                    "oid": "G.DM.DM",
                    "name": "General Demography",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000007",
                                "name": "locked",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "No",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                            {
                                "uid": "OdmVendorAttribute_000008",
                                "name": "connectivity",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "OdmVendorNamespace_000001",
                            },
                        ],
                    },
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000006",
                    "name": "allows",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "uds",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:52.562266+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000002",
            "name": "Vital Signs",
            "library_name": "Sponsor",
            "oid": "F.VS",
            "repeating": "No",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000037",
                    "name": "Vital signs form",
                    "language": "ENG",
                    "description": "Vital signs form",
                    "instruction": "form instruction",
                    "sponsor_instruction": "form sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [
                {
                    "uid": "OdmAlias_000001",
                    "context": "context1",
                    "name": "name1",
                    "version": "1.0",
                }
            ],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000004",
                    "oid": "G.VS.VS",
                    "name": "Vital Signs",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000007",
                                "name": "locked",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            }
                        ]
                    },
                },
                {
                    "uid": "OdmItemGroup_000001",
                    "oid": "G.VS.BPP",
                    "name": "Blood pressure and pulse",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000007",
                                "name": "locked",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            }
                        ]
                    },
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000006",
                    "name": "allows",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "second",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "item_groups": [
        {
            "start_date": "2022-12-01T13:06:50.310143+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000001",
            "name": "Blood pressure and pulse",
            "library_name": "Sponsor",
            "oid": "G.VS.BPP",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "VITALSIGNSBPP",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000032",
                    "name": "Blood pressure and pulse",
                    "language": "ENG",
                    "description": "Blood pressure and pulse",
                    "instruction": "item group instruction",
                    "sponsor_instruction": "item group sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [
                {
                    "uid": "OdmAlias_000001",
                    "context": "context1",
                    "name": "name1",
                    "version": "1.0",
                }
            ],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000023",
                    "oid": "I.SYSBP",
                    "name": "Systolic blood pressure",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "C.OID1",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000009",
                    "oid": "I.DIABP",
                    "name": "Diastolic blood pressure",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                            {
                                "uid": "OdmVendorAttribute_000005",
                                "name": "dataEntryRequired",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000014",
                    "oid": "I.POSITION",
                    "name": "Position",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000013",
                    "oid": "I.LATERALITY",
                    "name": "Laterality",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000002",
                    "oid": "I.LOC",
                    "name": "Anatomical Location",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000016",
                    "oid": "I.PULSE",
                    "name": "Pulse",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "gr",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "ig1",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:50.741764+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000002",
            "name": "General Demography",
            "library_name": "Sponsor",
            "oid": "G.DM.DM",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "DEMOG",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000033",
                    "name": "General Demographic item group",
                    "language": "ENG",
                    "description": "General Demographic item group",
                    "instruction": "item group instruction",
                    "sponsor_instruction": "item group sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [
                {
                    "uid": "OdmAlias_000002",
                    "context": "context2",
                    "name": "name2",
                    "version": "1.0",
                }
            ],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000007",
                    "oid": "I.BRTHDTCARGUS",
                    "name": "Date of birth (only for Argus interface) [hidden]",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "C.OID2",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000006",
                    "oid": "I.BRTHDTC",
                    "name": "Date of birth",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": "M.OID1",
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000001",
                    "oid": "I.AGE",
                    "name": "Age",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000020",
                    "oid": "I.SEX",
                    "name": "Sex [read-only]",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000019",
                    "oid": "I.SEXDEA",
                    "name": "Sex [de-activated]",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000010",
                    "oid": "I.ETHNIC",
                    "name": "Ethnicity",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000017",
                    "oid": "I.RACE",
                    "name": "Race",
                    "order_number": 7,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000018",
                    "oid": "I.RACEOTH",
                    "name": "Race other",
                    "order_number": 8,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000022",
                    "oid": "I.SUBJID",
                    "name": "Subject No. [read-only]",
                    "order_number": 9,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000015",
                    "oid": "I.PREVSUBJ",
                    "name": "Previous Subject No.",
                    "order_number": 10,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "gr",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "ig2",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:51.083170+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000003",
            "name": "Informed Consent",
            "library_name": "Sponsor",
            "oid": "G.DM.IC",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "DEMOG",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000034",
                    "name": "Informed Consent item group",
                    "language": "ENG",
                    "description": "Informed Consent item group",
                    "instruction": "item group instruction",
                    "sponsor_instruction": "item group sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000021",
                    "oid": "I.STUDYID",
                    "name": "Study ID",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000003",
                    "oid": "I.RFICDAT",
                    "name": "Date informed consent obtained",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000024",
                    "oid": "I.RFICTIM",
                    "name": "Time informed consent obtained",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000005",
                    "oid": "I.RFICDATLAR1",
                    "name": "Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) [de-activated]",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000011",
                    "oid": "I.RFICTIMLAR1",
                    "name": "Informed Consent TIME obtained by Parents/Legally Acceptable Representative (LAR) [de-activated]",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000004",
                    "oid": "I.RFICDATLAR2",
                    "name": "Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated]",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000012",
                    "oid": "I.RFICTIMLAR2",
                    "name": "Informed Consent Time obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated]",
                    "order_number": 7,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "gr",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "ig3",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:51.344606+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000004",
            "name": "Vital Signs",
            "library_name": "Sponsor",
            "oid": "G.VS.VS",
            "repeating": "Yes",
            "is_reference_data": "No",
            "sas_dataset_name": "VITALSIGNS",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000035",
                    "name": "Vital signs",
                    "language": "ENG",
                    "description": "Vital signs",
                    "instruction": "item group instruction",
                    "sponsor_instruction": "item group sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000021",
                    "oid": "I.STUDYID",
                    "name": "Study ID",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000022",
                    "oid": "I.SUBJID",
                    "name": "Subject No. [read-only]",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
                {
                    "uid": "OdmItem_000008",
                    "oid": "I.VSDAT",
                    "name": "Date of examination",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "sdv",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "Yes",
                                "vendor_namespace_uid": "odm_vendor_namespace2",
                            },
                        ]
                    },
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "gr",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "ig4",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "items": [
        {
            "start_date": "2022-12-01T13:06:43.535561+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000001",
            "name": "Age",
            "library_name": "Sponsor",
            "oid": "I.AGE",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "AGE",
            "sds_var_name": "AGE",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000008",
                    "name": "Age",
                    "language": "ENG",
                    "description": "Age",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": {
                "uid": "editable_cr",
                "name": "codelist attributes value1",
                "submission_value": "codelist submission value1",
                "preferred_term": "codelist preferred term",
            },
            "terms": [
                {
                    "term_uid": "term_root_final",
                    "name": "term_value_name1",
                    "mandatory": False,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                }
            ],
            "activity": None,
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "Sometag",
                    "value": "inner text",
                }
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "allowsMultiChoice",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "true",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [
                {
                    "uid": "OdmVendorAttribute_000002",
                    "name": "someAttr",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "a value",
                    "vendor_element_uid": "OdmVendorElement_000001",
                }
            ],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:43.858569+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000002",
            "name": "Anatomical Location",
            "library_name": "Sponsor",
            "oid": "I.LOC",
            "prompt": "",
            "datatype": "string",
            "length": 15,
            "significant_digits": None,
            "sas_field_name": "LOCATION",
            "sds_var_name": "VSLOC where VSTESTCD=SYSBP | VSLOC where VSTESTCD=DIABP",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000009",
                    "name": "Anatomical Location",
                    "language": "ENG",
                    "description": "Anatomical Location of the measurement",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "Sometag",
                    "value": "inner text",
                }
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "allowsMultiChoice",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "false",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [
                {
                    "uid": "OdmVendorAttribute_000002",
                    "name": "someAttr",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "a value",
                    "vendor_element_uid": "OdmVendorElement_000001",
                }
            ],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:44.093541+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000003",
            "name": "Date informed consent obtained",
            "library_name": "Sponsor",
            "oid": "I.RFICDAT",
            "prompt": "",
            "datatype": "date",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "RFICDAT",
            "sds_var_name": "RFICDTC, DSSTDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000010",
                    "name": "Date informed consent obtained",
                    "language": "ENG",
                    "description": "Informed Consent DATE",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:44.357431+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000004",
            "name": "Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated]",
            "library_name": "Sponsor",
            "oid": "I.RFICDATLAR2",
            "prompt": "",
            "datatype": "date",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "RFICDAT",
            "sds_var_name": "RFICDTC, DSSTDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000011",
                    "name": "Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated ]",
                    "language": "ENG",
                    "description": "Informed Consent DATE (Legal or authorised representative 2)",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:44.614561+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000005",
            "name": "Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) [de-activated]",
            "library_name": "Sponsor",
            "oid": "I.RFICDATLAR1",
            "prompt": "",
            "datatype": "date",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "RFICDAT",
            "sds_var_name": "RFICDTC, DSSTDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000012",
                    "name": "Date informed consent obtained by Parents/Legally Acceptable Representative (LAR) [de-activated ]",
                    "language": "ENG",
                    "description": "Informed Consent Date (Legal or authorised representative 1)",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:44.889252+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000006",
            "name": "Date of birth",
            "library_name": "Sponsor",
            "oid": "I.BRTHDTC",
            "prompt": "",
            "datatype": "date",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "BRTHDAT",
            "sds_var_name": "BRTHDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000013",
                    "name": "Date of birth",
                    "language": "ENG",
                    "description": "Date of birth",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:45.121390+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000007",
            "name": "Date of birth (only for Argus interface) [hidden]",
            "library_name": "Sponsor",
            "oid": "I.BRTHDTCARGUS",
            "prompt": "",
            "datatype": "date",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "BRTHDAT",
            "sds_var_name": "BRTHDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000014",
                    "name": "Date of birth (only for Argus interface) [hidden ]",
                    "language": "ENG",
                    "description": "Date of birth (only for Argus interface) [hidden ]",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:45.371058+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000008",
            "name": "Date of examination",
            "library_name": "Sponsor",
            "oid": "I.VSDAT",
            "prompt": "",
            "datatype": "date",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "VSDAT",
            "sds_var_name": "VSDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000015",
                    "name": "Date of examination",
                    "language": "ENG",
                    "description": "Date of examination [de-activated ]",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:45.665150+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000009",
            "name": "Diastolic blood pressure",
            "library_name": "Sponsor",
            "oid": "I.DIABP",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "BP_DIASTOLIC",
            "sds_var_name": "VSORRES where VSTESTCD=DIABP, VSORRESU where VSTESTCD=DIABP",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000016",
                    "name": "Diastolic blood pressure",
                    "language": "ENG",
                    "description": "Diastolic blood pressure",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:45.912130+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000010",
            "name": "Ethnicity",
            "library_name": "Sponsor",
            "oid": "I.ETHNIC",
            "prompt": "",
            "datatype": "string",
            "length": 20,
            "significant_digits": None,
            "sas_field_name": "ETHNIC",
            "sds_var_name": "ETHNIC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000017",
                    "name": "Ethnicity",
                    "language": "ENG",
                    "description": "Ethinicity",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:46.204779+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000011",
            "name": "Informed Consent TIME obtained by Parents/Legally Acceptable Representative (LAR) [de-activated]",
            "library_name": "Sponsor",
            "oid": "I.RFICTIMLAR1",
            "prompt": "",
            "datatype": "time",
            "length": 5,
            "significant_digits": None,
            "sas_field_name": "RFICTIM",
            "sds_var_name": "RFICDTC, DSSTDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000018",
                    "name": "Informed Consent TIME obtained by Parents/Legally Acceptable Representative (LAR) [de-activated ]",
                    "language": "ENG",
                    "description": "Informed Consent Time (Legal or authorised representative 1)",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:46.450125+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000012",
            "name": "Informed Consent Time obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated]",
            "library_name": "Sponsor",
            "oid": "I.RFICTIMLAR2",
            "prompt": "",
            "datatype": "time",
            "length": 5,
            "significant_digits": None,
            "sas_field_name": "RFICTIM",
            "sds_var_name": "RFICDTC, DSSTDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000019",
                    "name": "Informed Consent Time obtained by Parents/Legally Acceptable Representative (LAR) Only to be completed in countries where Informed Consent from both parents is required [de-activated ]",
                    "language": "ENG",
                    "description": "Informed Consent Time (Legal or authorised representative 2)",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:46.672706+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000013",
            "name": "Laterality",
            "library_name": "Sponsor",
            "oid": "I.LATERALITY",
            "prompt": "",
            "datatype": "string",
            "length": 15,
            "significant_digits": None,
            "sas_field_name": "LATERALITY",
            "sds_var_name": "VSLAT where VSTESTCD=SYSBP | VSLAT where VSTESTCD=DIABP",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000020",
                    "name": "Laterality",
                    "language": "ENG",
                    "description": "Laterality of the measurement",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:46.898643+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000014",
            "name": "Position",
            "library_name": "Sponsor",
            "oid": "I.POSITION",
            "prompt": "",
            "datatype": "string",
            "length": 15,
            "significant_digits": None,
            "sas_field_name": "POSITION",
            "sds_var_name": "VSPOS where VSTESTCD=SYSBP | VSPOS where VSTESTCD=DIABP",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000021",
                    "name": "Position",
                    "language": "ENG",
                    "description": "Position of the subject",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:47.144663+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000015",
            "name": "Previous Subject No.",
            "library_name": "Sponsor",
            "oid": "I.PREVSUBJ",
            "prompt": "",
            "datatype": "string",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "PREVSUBJ",
            "sds_var_name": "PREVSUBJ",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000022",
                    "name": "Previous Subject No.",
                    "language": "ENG",
                    "description": "Previous Subject No.",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:47.432811+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000016",
            "name": "Pulse",
            "library_name": "Sponsor",
            "oid": "I.PULSE",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "PULSE",
            "sds_var_name": "VSORRES/VSORRESU when VSTESTCD=PULSE",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000023",
                    "name": "Pulse",
                    "language": "ENG",
                    "description": "Pulse",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:47.673997+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000017",
            "name": "Race",
            "library_name": "Sponsor",
            "oid": "I.RACE",
            "prompt": "",
            "datatype": "string",
            "length": 40,
            "significant_digits": None,
            "sas_field_name": "RACE",
            "sds_var_name": "RACE",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000024",
                    "name": "Race",
                    "language": "ENG",
                    "description": "Race",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:47.891876+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000018",
            "name": "Race other",
            "library_name": "Sponsor",
            "oid": "I.RACEOTH",
            "prompt": "",
            "datatype": "string",
            "length": 40,
            "significant_digits": None,
            "sas_field_name": "RACEOTH",
            "sds_var_name": "RACEOTH in SUPPDM",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000025",
                    "name": "Race other",
                    "language": "ENG",
                    "description": "Race other",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:48.115166+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000019",
            "name": "Sex [de-activated]",
            "library_name": "Sponsor",
            "oid": "I.SEXDEA",
            "prompt": "",
            "datatype": "string",
            "length": 15,
            "significant_digits": None,
            "sas_field_name": "SEX",
            "sds_var_name": "SEX",
            "origin": "Protocol Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000026",
                    "name": "Sex [de-activated ]",
                    "language": "ENG",
                    "description": "Sex [de-activated ]",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:48.352891+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000020",
            "name": "Sex [read-only]",
            "library_name": "Sponsor",
            "oid": "I.SEX",
            "prompt": "",
            "datatype": "string",
            "length": 15,
            "significant_digits": None,
            "sas_field_name": "SEX",
            "sds_var_name": "SEX",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000027",
                    "name": "Sex [read-only ]",
                    "language": "ENG",
                    "description": "Sex [read-only ]",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:48.674244+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000021",
            "name": "Study ID",
            "library_name": "Sponsor",
            "oid": "I.STUDYID",
            "prompt": "",
            "datatype": "string",
            "length": 11,
            "significant_digits": None,
            "sas_field_name": "STUDYID",
            "sds_var_name": "STUDYID",
            "origin": "Protocol Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000028",
                    "name": "Study ID",
                    "language": "ENG",
                    "description": "Study Identifier",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "editable_cr",
                "name": "codelist attributes value1",
                "submission_value": "codelist submission value1",
                "preferred_term": "codelist preferred term",
            },
            "terms": [
                {
                    "term_uid": "term_root_final",
                    "name": "term_value_name1",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                }
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:48.908369+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000022",
            "name": "Subject No. [read-only]",
            "library_name": "Sponsor",
            "oid": "I.SUBJID",
            "prompt": "",
            "datatype": "string",
            "length": 10,
            "significant_digits": None,
            "sas_field_name": "SUBJID",
            "sds_var_name": "SUBJID",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000029",
                    "name": "Subject No. [read-only ]",
                    "language": "ENG",
                    "description": "Subject No.",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:49.192677+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000023",
            "name": "Systolic blood pressure",
            "library_name": "Sponsor",
            "oid": "I.SYSBP",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "BP_SYSTOLIC",
            "sds_var_name": "VSORRES where VSTESTCD=SYSBP, VSORRESU where VSTESTCD=SYSBP",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000030",
                    "name": "Systolic blood pressure",
                    "language": "ENG",
                    "description": "Systolic blood pressure",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:49.426734+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000024",
            "name": "Time informed consent obtained",
            "library_name": "Sponsor",
            "oid": "I.RFICTIM",
            "prompt": "",
            "datatype": "time",
            "length": 5,
            "significant_digits": None,
            "sas_field_name": "RFICTIM",
            "sds_var_name": "RFICDTC, DSSTDTC",
            "origin": "Collected Value",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000031",
                    "name": "Time informed consent obtained",
                    "language": "ENG",
                    "description": "Informed Consent time",
                    "instruction": "item instruction",
                    "sponsor_instruction": "item sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "conditions": [
        {
            "start_date": "2022-12-01T13:06:39.782910+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmCondition_000001",
            "name": "Condition1",
            "library_name": "Sponsor",
            "oid": "C.OID1",
            "formal_expressions": [
                {
                    "uid": "OdmFormalExpression_000001",
                    "context": "XPath",
                    "expression": "Formal Expression 1",
                    "version": "2.0",
                }
            ],
            "descriptions": [
                {
                    "uid": "OdmDescription_000004",
                    "name": "Condition 1 Description Name",
                    "language": "ENG",
                    "description": "Condition 1 Description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-01T13:06:40.525073+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmCondition_000002",
            "name": "Condition2",
            "library_name": "Sponsor",
            "oid": "C.OID2",
            "formal_expressions": [
                {
                    "uid": "OdmFormalExpression_000002",
                    "context": "XPath",
                    "expression": "Formal Expression 2",
                    "version": "1.0",
                }
            ],
            "descriptions": [
                {
                    "uid": "OdmDescription_000005",
                    "name": "Condition 2 Description Name",
                    "language": "ENG",
                    "description": "Condition 2 Description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                },
                {
                    "uid": "OdmDescription_000006",
                    "name": "Condition 3 Description Name",
                    "language": "DAN",
                    "description": "Condition 3 Description",
                    "instruction": None,
                    "sponsor_instruction": None,
                    "version": "1.0",
                },
                {
                    "uid": "OdmDescription_000007",
                    "name": "Condition 4 Description Name",
                    "language": "ARA",
                    "description": "Please update this description",
                    "instruction": None,
                    "sponsor_instruction": None,
                    "version": "1.0",
                },
            ],
            "aliases": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "methods": [
        {
            "start_date": "2022-12-01T13:06:39.067077+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmMethod_000001",
            "name": "Method1",
            "library_name": "Sponsor",
            "oid": "M.OID1",
            "method_type": "Method1",
            "formal_expressions": [
                {
                    "uid": "OdmFormalExpression_000001",
                    "context": "XPath",
                    "expression": "Formal Expression 1",
                    "version": "2.0",
                }
            ],
            "descriptions": [
                {
                    "uid": "OdmDescription_000003",
                    "name": "Method 1 Description Name",
                    "language": "ARA",
                    "description": "Please update this description",
                    "instruction": None,
                    "sponsor_instruction": None,
                    "version": "1.0",
                },
                {
                    "uid": "OdmDescription_000001",
                    "name": "Method 2 Description Name",
                    "language": "ENG",
                    "description": "Method 1 Description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                },
                {
                    "uid": "OdmDescription_000002",
                    "name": "Method 3 Description Name",
                    "language": "DAN",
                    "description": "Method 2 Description",
                    "instruction": None,
                    "sponsor_instruction": None,
                    "version": "1.0",
                },
            ],
            "aliases": [],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
}
import_input2 = """<?xml version="1.0" encoding="utf-8"?>
        <ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="url2" xmlns:cs="http://clinspark.org" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1666353293513" CreationDateTime="2022-10-21 13:54:53.513447" Granularity="All">
            <Study OID="ODM version 1.3.2 with DoB-T.ODM-1-3-2-V1">
                <GlobalVariables>
                    <ProtocolName>ODM version 1.3.2 with DoB</ProtocolName>
                    <StudyName>ODM version 1.3.2 with DoB</StudyName>
                    <StudyDescription>ODM version 1.3.2 with DoB</StudyDescription>
                </GlobalVariables>
                <BasicDefinitions/>
                <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                    <FormDef OID="oid1" Name="name1" Repeated="Yes" osb:newAttribute="someValue" CompletionInstructions="instruction1" ImplementationNotes="sponsor_instruction1">
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                        </Description>
                        <NameOne>test value</NameOne>
                        <Alias Name="instruction1" Context="CompletionInstructions" />
                        <Alias Name="sponsor_instruction1" Context="ImplementationNotes" />
                    </FormDef>
                </MetaDataVersion>
            </Study>
        </ODM>"""
import_output2 = {
    "vendor_namespaces": [
        {
            "start_date": "2022-11-18T11:01:34.916840",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorNamespace_000001",
            "name": "CS",
            "library_name": "Sponsor",
            "prefix": "cs",
            "url": "http://clinspark.org",
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "nameOne",
                    "compatible_types": ["FormDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                }
            ],
            "vendor_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-11-18T10: 22: 40.793493",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_namespace2",
            "name": "OSB",
            "library_name": "Sponsor",
            "prefix": "osb",
            "url": "url2",
            "vendor_elements": [
                {
                    "uid": "odm_vendor_element2",
                    "name": "nameTwo",
                    "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                }
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "newAttribute",
                    "data_type": "string",
                    "compatible_types": ["FormDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                }
            ],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "vendor_attributes": [
        {
            "start_date": "2022-11-18T10:29:58.815197",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000001",
            "name": "newAttribute",
            "library_name": "Sponsor",
            "compatible_types": ["FormDef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
    "vendor_elements": [
        {
            "start_date": "2022-11-18T11:04:33.435405",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorElement_000001",
            "name": "nameOne",
            "library_name": "Sponsor",
            "vendor_namespace": {
                "uid": "OdmVendorNamespace_000001",
                "name": "CS",
                "prefix": "cs",
                "url": "http://clinspark.org",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_attributes": [],
            "compatible_types": ["FormDef"],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-12T09:16:09.313000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_element2",
            "name": "nameTwo",
            "library_name": "Sponsor",
            "vendor_namespace": {
                "uid": "odm_vendor_namespace2",
                "name": "OSB",
                "prefix": "osb",
                "url": "url2",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_attributes": [],
            "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "study_events": [
        {
            "start_date": "2022-11-28T13:16:19.962283",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmStudyEvent_000001",
            "name": "ODM version 1.3.2 with DoB",
            "library_name": "Sponsor",
            "oid": "ODM version 1.3.2 with DoB",
            "effective_date": None,
            "retired_date": None,
            "description": None,
            "display_in_tree": True,
            "forms": [
                {
                    "uid": "OdmForm_000001",
                    "name": "name1",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                }
            ],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
    "forms": [
        {
            "start_date": "2022-11-18T10:22:42.344278",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000001",
            "name": "name1",
            "library_name": "Sponsor",
            "oid": "oid1",
            "repeating": "Yes",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000001",
                    "name": "description1",
                    "language": "ENG",
                    "description": "description1",
                    "instruction": "instruction1",
                    "sponsor_instruction": "sponsor_instruction1",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "activity_groups": [],
            "item_groups": [],
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "nameOne",
                    "value": "test value",
                }
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "newAttribute",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "someValue",
                    "vendor_namespace_uid": "odm_vendor_namespace2",
                }
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
    "item_groups": [],
    "items": [],
    "conditions": [],
    "methods": [],
}
import_input3 = """<?xml version="1.0" encoding="utf-8"?>
        <ODM ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1666353293513" CreationDateTime="2022-10-21 13:54:53.513447" Granularity="All">
            <Study OID="ODM version 1.3.2 with DoB-T.ODM-1-3-2-V1">
                <GlobalVariables>
                    <ProtocolName>ODM version 1.3.2 with DoB</ProtocolName>
                    <StudyName>ODM version 1.3.2 with DoB</StudyName>
                    <StudyDescription>ODM version 1.3.2 with DoB</StudyDescription>
                </GlobalVariables>
                <BasicDefinitions>
                    <MeasurementUnit OID="wrong name" Name="a name">
                        <Symbol>
                        <TranslatedText xml:lang="en">a name</TranslatedText>
                        </Symbol>
                    </MeasurementUnit>
                </BasicDefinitions>
                <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version" />
            </Study>
        </ODM>"""
import_input4 = """<?xml version="1.0" encoding="utf-8"?>
        <ODM ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1666353293513" CreationDateTime="2022-10-21 13:54:53.513447" Granularity="All" xmlns:prefix="url1">
            <Study OID="ODM version 1.3.2 with DoB-T.ODM-1-3-2-V1">
                <GlobalVariables>
                    <ProtocolName>ODM version 1.3.2 with DoB</ProtocolName>
                    <StudyName>ODM version 1.3.2 with DoB</StudyName>
                    <StudyDescription>ODM version 1.3.2 with DoB</StudyDescription>
                </GlobalVariables>
                <BasicDefinitions/>
                <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                    <FormDef OID="oid1" Name="name1" Repeating="Yes" prefix:nameThree="1234" />
                </MetaDataVersion>
            </Study>
        </ODM>"""
import_input5 = """<?xml version="1.0" encoding="utf-8"?>
        <ODM ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1666353293513" CreationDateTime="2022-10-21 13:54:53.513447" Granularity="All" xmlns:prefix="url1">
            <Study OID="ODM version 1.3.2 with DoB-T.ODM-1-3-2-V1">
                <GlobalVariables>
                    <ProtocolName>ODM version 1.3.2 with DoB</ProtocolName>
                    <StudyName>ODM version 1.3.2 with DoB</StudyName>
                    <StudyDescription>ODM version 1.3.2 with DoB</StudyDescription>
                </GlobalVariables>
                <BasicDefinitions/>
                <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                    <FormDef OID="oid1" Name="name1" Repeating="Yes">
                        <ItemGroupRef prefix:nameThree="1234" ItemGroupOID="G.1" Mandatory="Yes" OrderNumber="6"/>
                    </FormDef>
                    <ItemGroupDef OID="G.1" Name="Blood pressure and pulse" Repeating="No" Purpose="Tabulation" SASDatasetName="VITALSIGNSBPP" Domain="VS:Vital Signs Domain"/>
                </MetaDataVersion>
            </Study>
        </ODM>"""
import_input6 = """<?xml version="1.0" encoding="utf-8"?>
        <?xml-stylesheet type="text/xsl" href="odm_study_event_sdtmcrf.xsl"?>
        <ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" ODMVersion="1.3.2" FileType="Snapshot" FileOID="OID.1666353293513" CreationDateTime="2022-10-21 13:54:53.513447" Granularity="All" xmlns:osb="url2" xmlns:clinspark="https://www.clinspark.com">
            <Study OID="ODM version 1.3.2 with DoB-T.ODM-1-3-2-V1">
                <GlobalVariables>
                    <ProtocolName>ODM version 1.3.2 with DoB</ProtocolName>
                    <StudyName>ODM version 1.3.2 with DoB</StudyName>
                    <StudyDescription>ODM version 1.3.2 with DoB</StudyDescription>
                </GlobalVariables>
                <BasicDefinitions/>
                <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                    <FormDef OID="F.DM" Name="Informed Consent and Demography" Repeating="No" osb:version="1.0" osb:instruction="form instruction" osb:sponsorInstruction="form sponsor instruction" osb:allows="uds">
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Informed Consent and Demography form</TranslatedText>
                        </Description>
                        <ItemGroupRef ItemGroupOID="G.DM.IC" Mandatory="Yes" OrderNumber="1" osb:locked="Yes" clinspark:connectivity="Yes" />
                        <ItemGroupRef ItemGroupOID="G.DM.DM" Mandatory="Yes" OrderNumber="2" osb:locked="No" clinspark:connectivity="Yes" />
                    </FormDef>
                    <ItemGroupDef OID="G.VS.BPP" Name="Blood pressure and pulse" Repeating="No" Purpose="Tabulation" SASDatasetName="VITALSIGNSBPP" Domain="VS:Vital Signs Domain">
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Blood pressure and pulse</TranslatedText>
                        </Description>
                        <ItemRef ItemOID="I.SYSBP" Mandatory="Yes" OrderNumber="1" CollectionExceptionConditionOID="C.OID1" osb:sdv="Yes" />
                    </ItemGroupDef>
                    <ItemDef OID="I.SYSBP" Name="Systolic blood pressure" Origin="Collected Value" DataType="integer" Length="3" SASFieldName="BP_SYSTOLIC" SDSVarName="VSORRES where VSTESTCD=SYSBP, VSORRESU where VSTESTCD=SYSBP" osb:version="1.0" osb:instruction="item instruction" osb:sponsorInstruction="item sponsor instruction">
                        <Question>
                            <TranslatedText xml:lang="en" osb:version="0.1">Systolic blood pressure</TranslatedText>
                        </Question>
                        <Description>
                            <TranslatedText xml:lang="en" osb:version="0.1">Systolic blood pressure</TranslatedText>
                        </Description>
                        <MeasurementUnitRef MeasurementUnitOID="name1" />
                    </ItemDef>
                </MetaDataVersion>
            </Study>
        </ODM>"""

clinspark_input = """<?xml version="1.0" encoding="UTF-8"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" FileType="Snapshot" Granularity="Metadata" FileOID="ODM.1665487443144" CreationDateTime="2022-10-11T13:24:03+02:00" ODMVersion="1.3.2" xmlns:prefix="url1">
   <Study OID="S.2">
      <GlobalVariables>
         <StudyName>Global Standards CRF Library</StudyName>
         <StudyDescription />
         <ProtocolName>Global Standards CRF Library</ProtocolName>
      </GlobalVariables>



      
      <BasicDefinitions>
         <MeasurementUnit OID="MU.27" Name="name1">
            <Symbol>
               <TranslatedText xml:lang="en">name1</TranslatedText>
            </Symbol>
         </MeasurementUnit>
      </BasicDefinitions>




      <MetaDataVersion OID="SM.4" Name="Global Standards CRF Library Metadata">
         <FormDef OID="F.47" Name="Informed Consent" Repeating="No" prefix:clinAttribute="form value">
            <ItemGroupRef ItemGroupOID="IG.124" OrderNumber="1" Mandatory="Yes" prefix:clinRefAttribute="item grouop ref" />
            <prefix:ClinTag prefix:clinVendorElementAttribute="vendor element attribute value">vendor element value</prefix:ClinTag>
         </FormDef>
         <FormDef OID="F.98" Name="Demography" Repeating="Yes">
            <ItemGroupRef ItemGroupOID="IG.262" OrderNumber="1" Mandatory="Yes" />
         </FormDef>
         <FormDef OID="F.52" Name="Body Measurements (with BMI)" Repeating="Yes">
            <Description>
               <TranslatedText xml:lang="en">Body Measurements form including weight, height and BMI calculation. Expected use for screening visit.</TranslatedText>
            </Description>
            <ItemGroupRef ItemGroupOID="IG.153" OrderNumber="2" Mandatory="Yes" />
         </FormDef>
         <FormDef OID="F.37" Name="Vital Signs (Single Measurement)" Repeating="Yes">
            <ItemGroupRef ItemGroupOID="IG.72" OrderNumber="1" Mandatory="Yes" />
         </FormDef>
         <FormDef OID="F.38" Name="Administration of &lt;Investigational medicinal product&gt;" Repeating="Yes">
            <ItemGroupRef ItemGroupOID="IG.97" OrderNumber="1" Mandatory="Yes" />
            <ItemGroupRef ItemGroupOID="IG.98" OrderNumber="2" Mandatory="Yes" />
            <ItemGroupRef ItemGroupOID="IG.99" OrderNumber="3" Mandatory="Yes" />
            <ItemGroupRef ItemGroupOID="IG.267" OrderNumber="4" Mandatory="Yes" />
         </FormDef>




         <ItemGroupDef OID="IG.124" Name="Informed Consent" Repeating="No" Domain="DS" Purpose="Tabulation" prefix:newClinAttribute="item group attr">
            <ItemRef ItemOID="I.579" OrderNumber="1" Mandatory="Yes" />
            <ItemRef ItemOID="I.661" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.566" OrderNumber="3" Mandatory="Yes" />
            <ItemRef ItemOID="I.567" OrderNumber="4" Mandatory="Yes" />
            <ItemRef ItemOID="I.568" OrderNumber="5" Mandatory="No" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.262" Name="Demography" Repeating="No" Domain="DM" Purpose="Tabulation">
            <Description>
               <TranslatedText xml:lang="en">Demographics</TranslatedText>
            </Description>
            <ItemRef ItemOID="I.1056" OrderNumber="1" Mandatory="Yes" />
            <ItemRef ItemOID="I.1057" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.1058" OrderNumber="3" Mandatory="No" />
            <ItemRef ItemOID="I.1059" OrderNumber="4" Mandatory="No" />
            <ItemRef ItemOID="I.1060" OrderNumber="5" Mandatory="No" />
            <ItemRef ItemOID="I.1061" OrderNumber="6" Mandatory="No" />
            <ItemRef ItemOID="I.1062" OrderNumber="7" Mandatory="No" />
            <ItemRef ItemOID="I.1063" OrderNumber="8" Mandatory="Yes" />
            <ItemRef ItemOID="I.1260" OrderNumber="9" Mandatory="Yes" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.153" Name="Body Measurements" Repeating="No" Domain="VS" Purpose="Tabulation">
            <Description>
               <TranslatedText xml:lang="en">Body Measurements</TranslatedText>
            </Description>
            <ItemRef ItemOID="I.596" OrderNumber="1" Mandatory="Yes" />
            <ItemRef ItemOID="I.597" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.637" OrderNumber="3" Mandatory="Yes" />
            <ItemRef ItemOID="I.600" OrderNumber="4" Mandatory="Yes" />
            <ItemRef ItemOID="I.601" OrderNumber="5" Mandatory="Yes" />
            <ItemRef ItemOID="I.621" OrderNumber="6" Mandatory="Yes" MethodOID="M.2" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.72" Name="Vital Signs" Repeating="No" Domain="VS" Purpose="Tabulation">
            <Description>
               <TranslatedText xml:lang="en">Vital Signs</TranslatedText>
            </Description>
            <ItemRef ItemOID="I.406" OrderNumber="1" Mandatory="Yes" />
            <ItemRef ItemOID="I.354" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.355" OrderNumber="4" Mandatory="Yes" />
            <ItemRef ItemOID="I.356" OrderNumber="5" Mandatory="Yes" />
            <ItemRef ItemOID="I.347" OrderNumber="6" Mandatory="Yes" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.97" Name="Prescribed dose of &lt;Investigational medicinal product&gt;" Repeating="No" Domain="EC" Purpose="Tabulation">
            <Description>
               <TranslatedText xml:lang="en">Exposure as Collected</TranslatedText>
            </Description>
            <ItemRef ItemOID="I.754" OrderNumber="1" Mandatory="Yes" MethodOID="M.34" />
            <ItemRef ItemOID="I.471" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.473" OrderNumber="3" Mandatory="Yes" />
            <ItemRef ItemOID="I.475" OrderNumber="4" Mandatory="Yes" />
            <ItemRef ItemOID="I.474" OrderNumber="5" Mandatory="Yes" />
            <ItemRef ItemOID="I.595" OrderNumber="6" Mandatory="Yes" />
            <ItemRef ItemOID="I.559" OrderNumber="7" Mandatory="Yes" />
            <ItemRef ItemOID="I.561" OrderNumber="8" Mandatory="Yes" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.98" Name="Preparation for dosing" Repeating="No" Purpose="Tabulation">
            <ItemRef ItemOID="I.585" OrderNumber="1" Mandatory="Yes" />
            <ItemRef ItemOID="I.586" OrderNumber="2" Mandatory="No" />
            <ItemRef ItemOID="I.588" OrderNumber="3" Mandatory="Yes" />
            <ItemRef ItemOID="I.592" OrderNumber="4" Mandatory="Yes" />
            <ItemRef ItemOID="I.593" OrderNumber="5" Mandatory="Yes" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.99" Name="Administration of &lt;Investigational medicinal product&gt;" Repeating="No" Domain="EC" Purpose="Tabulation">
            <Description>
               <TranslatedText xml:lang="en">Exposure as Collected</TranslatedText>
            </Description>
            <ItemRef ItemOID="I.754" OrderNumber="1" Mandatory="Yes" MethodOID="M.34" />
            <ItemRef ItemOID="I.471" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.473" OrderNumber="3" Mandatory="Yes" />
            <ItemRef ItemOID="I.475" OrderNumber="4" Mandatory="Yes" />
            <ItemRef ItemOID="I.474" OrderNumber="5" Mandatory="Yes" />
            <ItemRef ItemOID="I.565" OrderNumber="6" Mandatory="Yes" />
            <ItemRef ItemOID="I.578" OrderNumber="7" Mandatory="Yes" />
            <ItemRef ItemOID="I.576" OrderNumber="8" Mandatory="Yes" />
            <ItemRef ItemOID="I.580" OrderNumber="9" Mandatory="Yes" />
            <ItemRef ItemOID="I.581" OrderNumber="10" Mandatory="Yes" />
            <ItemRef ItemOID="I.582" OrderNumber="11" Mandatory="Yes" />
            <ItemRef ItemOID="I.583" OrderNumber="12" Mandatory="Yes" />
            <ItemRef ItemOID="I.560" OrderNumber="13" Mandatory="Yes" />
            <ItemRef ItemOID="I.561" OrderNumber="14" Mandatory="Yes" />
            <ItemRef ItemOID="I.562" OrderNumber="15" Mandatory="Yes" />
            <ItemRef ItemOID="I.563" OrderNumber="16" Mandatory="Yes" />
            <ItemRef ItemOID="I.564" OrderNumber="17" Mandatory="Yes" />
         </ItemGroupDef>
         <ItemGroupDef OID="IG.267" Name="Post dose" Repeating="No" Purpose="Tabulation">
            <ItemRef ItemOID="I.589" OrderNumber="1" Mandatory="Yes" />
            <ItemRef ItemOID="I.590" OrderNumber="2" Mandatory="Yes" />
            <ItemRef ItemOID="I.594" OrderNumber="3" Mandatory="Yes" />
         </ItemGroupDef>




         <ItemDef OID="I.579" Name="DS_DSCAT" DataType="text" Length="18" SASFieldName="DSCAT" Origin="CRF" SDSVarName="DS:DSCAT">
            <Question>
               <TranslatedText xml:lang="en">DSCAT</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.72" />
         </ItemDef>
         <ItemDef OID="I.661" Name="DS_DSDECOD" DataType="text" Length="43" SASFieldName="DSDECOD" Origin="CRF" SDSVarName="DS:DSDECOD">
            <Question>
               <TranslatedText xml:lang="en">DSDECOD</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.75" />
         </ItemDef>
         <ItemDef OID="I.566" Name="ICFVER_eS" DataType="string" Length="200" Origin="Protocol" SDSVarName="DS:ICFVER">
            <Question>
               <TranslatedText xml:lang="en">ICF Version</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.567" Name="DS_inf_consent_DSSTDTC" DataType="datetime" SASFieldName="DSSTDTC" Origin="CRF" SDSVarName="DS:DSSTDTC">
            <Question>
               <TranslatedText xml:lang="en">Date and time informed consent obtained</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.568" Name="ICFNOTES_eS" DataType="text" Length="999" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">ICF Notes</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.596" Name="VS_fasting_FASTING" DataType="string" Length="1" SASFieldName="FASTING" Origin="CRF" Comment="Optional in eCRF" SDSVarName="VS:FASTING">
            <Question>
               <TranslatedText xml:lang="en">Was the subject fasting when the body measurement was done?</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.90" />
         </ItemDef>
         <ItemDef OID="I.597" Name="VS_VSCAT" DataType="text" Length="16" SASFieldName="VSCAT" Origin="CRF" SDSVarName="VS:VSCAT">
            <Question>
               <TranslatedText xml:lang="en">VSCAT</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.78" />
         </ItemDef>
         <ItemDef OID="I.637" Name="VS_date and time of exam_VSDTC" DataType="datetime" SASFieldName="VSDTC" Origin="CRF" SDSVarName="VS:VSDTC">
            <Question>
               <TranslatedText xml:lang="en">Date and time of examination</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.600" Name="VS_height_VSTESTCD-VSORRES" DataType="float" Length="1" SignificantDigits="2" SASFieldName="VSTESTCD" SDSVarName="HEIGHT" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Height</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
            <RangeCheck Comparator="GE" SoftHard="Hard">
               <CheckValue>0.00</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="GE" SoftHard="Soft">
               <CheckValue>1.40</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Soft">
               <CheckValue>2.20</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Hard">
               <CheckValue>3.50</CheckValue>
            </RangeCheck>
         </ItemDef>
         <ItemDef OID="I.601" Name="VS_weight_VSTESTCD-VSORRES" DataType="float" Length="3" SignificantDigits="2" SASFieldName="VSTESTCD" SDSVarName="WEIGHT" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Body weight</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
            <RangeCheck Comparator="GE" SoftHard="Hard">
               <CheckValue>0.00</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="GE" SoftHard="Soft">
               <CheckValue>30.00</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Soft">
               <CheckValue>350.00</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Hard">
               <CheckValue>1000.00</CheckValue>
            </RangeCheck>
         </ItemDef>
         <ItemDef OID="I.621" Name="VS_BMI_VSORRES-VSTESTCD" DataType="float" Length="4" SignificantDigits="1" SASFieldName="VSTESTCD" SDSVarName="BMI" Origin="Protocol" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">BMI</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
         </ItemDef>
         <ItemDef OID="I.1056" Name="DM_age_AGECOLL" DataType="integer" Length="3" SASFieldName="AGECOLL" Origin="CRF" SDSVarName="DM:AGE">
            <Description>
               <TranslatedText xml:lang="en">Age</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Age</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
         </ItemDef>
         <ItemDef OID="I.1057" Name="DM Sex" DataType="string" Length="100" SASFieldName="SEX" Origin="CRF" SDSVarName="DM:SEX">
            <Description>
               <TranslatedText xml:lang="en">Sex</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Sex</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.194" />
         </ItemDef>
         <ItemDef OID="I.1058" Name="DM Race - American Indian Or Alaska Native" DataType="boolean" SASFieldName="RACE1" Origin="CRF" SDSVarName="DM:RACE">
            <Description>
               <TranslatedText xml:lang="en">Race - American Indian Or Alaska Native</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Subject self-reported race - American Indian Or Alaska Native</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.1059" Name="DM Race - Asian" DataType="boolean" SASFieldName="RACE2" Origin="CRF" SDSVarName="DM:RACE">
            <Description>
               <TranslatedText xml:lang="en">Race - Asian</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Subject self-reported race - Asian</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.1060" Name="DM Race - Black Or African American" DataType="boolean" SASFieldName="RACE3" Origin="CRF" SDSVarName="DM:RACE">
            <Description>
               <TranslatedText xml:lang="en">Race - Black Or African American</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Subject self-reported race - Black or African American</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.1061" Name="DM Race - Native Hawaiian Or Other Pacific Islander" DataType="boolean" SASFieldName="RACE4" Origin="CRF" SDSVarName="DM:RACE">
            <Description>
               <TranslatedText xml:lang="en">Race - Native Hawaiian Or Other Pacific Islander</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Subject self-reported race - Native Hawaiian or Other Pacific Islander</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.1062" Name="DM Race - White" DataType="boolean" SASFieldName="RACE5" Origin="CRF" SDSVarName="DM:RACE">
            <Description>
               <TranslatedText xml:lang="en">Race - White</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Subject self-reported race - White</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.1063" Name="DM Ethnicity" DataType="string" Length="100" SASFieldName="ETHNIC" Origin="CRF" SDSVarName="DM:ETHNIC">
            <Description>
               <TranslatedText xml:lang="en">Ethnicity</TranslatedText>
            </Description>
            <Question>
               <TranslatedText xml:lang="en">Subject self-reported ethnicity</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.193" />
         </ItemDef>
         <ItemDef OID="I.1260" Name="DM_previous _subject_number_PREVSUBJ" DataType="integer" Length="6" SASFieldName="PREVSUBJ" Origin="CRF" Comment="Optional in the CRF" SDSVarName="DM:PREVUBJ">
            <Question>
               <TranslatedText xml:lang="en">Previous Subject No.</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.406" Name="VS_VSCAT" DataType="text" Length="16" SASFieldName="VSCAT" Origin="CRF" Comment="optional in CRF" SDSVarName="">
            <Question>
               <TranslatedText xml:lang="en">VSCAT</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.78" />
         </ItemDef>
         <ItemDef OID="I.354" Name="VS_date of exam_VSDTC" DataType="date" SASFieldName="VSDTC" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Date of examination</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.355" Name="VS_syst_blood_pres_ORRES_SYSBP" DataType="integer" Length="3" SASFieldName="VSTESTCD" SDSVarName="SYSBP" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Systolic blood pressure</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
            <RangeCheck Comparator="GE" SoftHard="Hard">
               <CheckValue>50</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="GE" SoftHard="Soft">
               <CheckValue>91</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Soft">
               <CheckValue>139</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Hard">
               <CheckValue>260</CheckValue>
            </RangeCheck>
         </ItemDef>
         <ItemDef OID="I.356" Name="VS_diast_blood_pres_ORRES_DIABP" DataType="integer" Length="3" SASFieldName="VSTESTCD" SDSVarName="DIABP" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Diastolic blood pressure</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
            <RangeCheck Comparator="GE" SoftHard="Hard">
               <CheckValue>31</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="GE" SoftHard="Soft">
               <CheckValue>52</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Soft">
               <CheckValue>90</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Hard">
               <CheckValue>201</CheckValue>
            </RangeCheck>
         </ItemDef>
         <ItemDef OID="I.347" Name="VS_pulse_ORRES_PULSE" DataType="integer" Length="3" SASFieldName="VSTESTCD" SDSVarName="PULSE" Origin="CRF" Comment="optional in CRF">
            <Question>
               <TranslatedText xml:lang="en">Pulse</TranslatedText>
            </Question>
            <RangeCheck Comparator="GE" SoftHard="Hard">
               <CheckValue>1</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="GE" SoftHard="Soft">
               <CheckValue>50</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Soft">
               <CheckValue>100</CheckValue>
            </RangeCheck>
            <RangeCheck Comparator="LE" SoftHard="Hard">
               <CheckValue>210</CheckValue>
            </RangeCheck>
            <Alias Context="CDASH" Name="PULSE.VSORRES" />
            <Alias Context="CDASH/SDTM" Name="VSORRES+VSORRESU" />
         </ItemDef>
         <ItemDef OID="I.754" Name="EC_seq_no_ECREFID" DataType="integer" Length="3" SASFieldName="ECREFID" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Seq. no.</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.471" Name="EC_ECCAT" DataType="string" Length="31" SASFieldName="ECCAT" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">ECCAT</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.105" />
         </ItemDef>
         <ItemDef OID="I.473" Name="EC_ECMOOD" DataType="string" Length="9" SASFieldName="ECMOOD" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">ECMOOD</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.99" />
         </ItemDef>
         <ItemDef OID="I.475" Name="EC_ECPRESP" DataType="string" Length="1" SASFieldName="ECPRESP" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">ECPRESP</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.107" />
         </ItemDef>
         <ItemDef OID="I.474" Name="EC_&lt;IMP&gt;_ECTRT" DataType="string" Length="7" SASFieldName="ECTRT" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">&lt;Investigational medicinal product&gt;</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.106" />
         </ItemDef>
         <ItemDef OID="I.595" Name="EC_datetime_prescription_ECSTDTC" DataType="partialDatetime" SASFieldName="ECSTDTC" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Start date and time of prescription</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.559" Name="EC_prescribed_dose_ECDOSE" DataType="integer" Length="3" SASFieldName="ECDOSE" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Prescribed dose</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.561" Name="EC_dose_form_ECDOSFRM" DataType="string" Length="9" SASFieldName="ECDOSFRM" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Dose form</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.100" />
         </ItemDef>
         <ItemDef OID="I.585" Name="EC_req_met_eS" DataType="string" Length="1" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Requirements for dosing met?</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.90" />
         </ItemDef>
         <ItemDef OID="I.586" Name="EC_morph_inj_site_eS" DataType="text" Length="200" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Morphology of injection site</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.588" Name="EC_dun_eS" DataType="integer" Length="6" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">DUN (Dispensing Unit No.)</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.592" Name="EC_no_inj_eS" DataType="integer" Length="1" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Number of injections</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.593" Name="EC_volume_eS" DataType="float" Length="4" SignificantDigits="1" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Volume administered</TranslatedText>
            </Question>
            <MeasurementUnitRef MeasurementUnitOID="MU.27" />
         </ItemDef>
         <ItemDef OID="I.565" Name="EC_adm_imp_ECOCCUR" DataType="string" Length="1" SASFieldName="ECOCCUR" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Has the investigational medicinal product been administered to the subject?</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.90" />
         </ItemDef>
         <ItemDef OID="I.578" Name="EC_specify_reason_ECREASOC" DataType="text" Length="200" SASFieldName="ECREASOC" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Specify reason</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.576" Name="EC_type_of_treatment_ECSCAT" DataType="string" Length="30" SASFieldName="ECSCAT" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Type of treatment</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.98" />
         </ItemDef>
         <ItemDef OID="I.580" Name="EC_bleed_no_ECXB" DataType="integer" Length="3" SASFieldName="ECXB" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Bleeding episode no.</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.581" Name="EC_surgery_no_ECPR" DataType="integer" Length="3" SASFieldName="ECPR" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Surgery no.</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.582" Name="EC_start_datetime_ECSTDTC" DataType="datetime" SASFieldName="ECSTDTC" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Start date and time of administration</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.583" Name="EC_end_datetime_ECENDTC" DataType="datetime" SASFieldName="ECENDTC" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">End date and time of administration</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.560" Name="EC_dose_ECDOSE" DataType="integer" Length="3" SASFieldName="ECDOSE" Origin="CRF">
            <Question>
               <TranslatedText xml:lang="en">Actual Dose</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.562" Name="EC_route_ECROUTE" DataType="string" Length="12" SASFieldName="ECROUTE" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Route</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.101" />
         </ItemDef>
         <ItemDef OID="I.563" Name="EC_laterality_ECLAT" DataType="string" Length="5" SASFieldName="ECLAT" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Laterality</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.102" />
         </ItemDef>
         <ItemDef OID="I.564" Name="EC_inj_site_ECLOC" DataType="string" Length="14" SASFieldName="ECLOC" Origin="CRF" Comment="Optional in eCRF">
            <Question>
               <TranslatedText xml:lang="en">Injection site</TranslatedText>
            </Question>
            <CodeListRef CodeListOID="CL.103" />
         </ItemDef>
         <ItemDef OID="I.589" Name="EC_admin_by_eS" DataType="text" Length="4" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Administered by</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.590" Name="EC_check_by_eS" DataType="text" Length="4" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Checked by</TranslatedText>
            </Question>
         </ItemDef>
         <ItemDef OID="I.594" Name="EC_comment_eS" DataType="text" Length="200" Origin="Protocol">
            <Question>
               <TranslatedText xml:lang="en">Comment</TranslatedText>
            </Question>
         </ItemDef>




         <CodeList OID="CL.90" Name="No Yes Response" DataType="string">
            <Description>
               <TranslatedText xml:lang="en">NY</TranslatedText>
            </Description>
            <CodeListItem CodedValue="Y" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Yes</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="N" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">No</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.72" Name="DS_DSCAT" DataType="text">
            <Description>
               <TranslatedText xml:lang="en">DSCAT</TranslatedText>
            </Description>
            <CodeListItem CodedValue="DISPOSITION EVENT" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Disposition event</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="PROTOCOL MILESTONE" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Protocol milestone</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="OTHER EVENT" Rank="3.00">
               <Decode>
                  <TranslatedText xml:lang="en">Other event</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.75" Name="DS_DSTERM" DataType="text">
            <Description>
               <TranslatedText xml:lang="en">NCOMPLT</TranslatedText>
            </Description>
            <CodeListItem CodedValue="FIRST DATE ON TRIAL PRODUCT" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">First date on trial product</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="LAST DATE ON TRIAL PRODUCT" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Last date on trial product</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="TREATMENT DISCONTINUATION" Rank="3.00">
               <Decode>
                  <TranslatedText xml:lang="en">Treatment discontinuation</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="TREATMENT UNBLINDED" Rank="4.00">
               <Decode>
                  <TranslatedText xml:lang="en">Treatment unblinded</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="INFORMED CONSENT OBTAINED" Rank="5.00">
               <Decode>
                  <TranslatedText xml:lang="en">Informed consent obtained</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="ELIGIBILITY CRITERIA MET" Rank="6.00">
               <Decode>
                  <TranslatedText xml:lang="en">Eligibility criteria met</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="RANDOMIZED" Rank="7.00">
               <Decode>
                  <TranslatedText xml:lang="en">Randomized</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="FUTURE RESEARCH BIOSAMPLE CONSENT OBTAINED" Rank="8.00">
               <Decode>
                  <TranslatedText xml:lang="en">Future research biosample consent obtained</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="FUTURE RESEARCH BIOSAMPLE CONSENT WITHDRAWN" Rank="9.00">
               <Decode>
                  <TranslatedText xml:lang="en">Future research biosample consent withdrawn</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.78" Name="VS_VSCAT" DataType="text">
            <Description>
               <TranslatedText xml:lang="en">VSCAT</TranslatedText>
            </Description>
            <CodeListItem CodedValue="VITAL SIGNS" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Vital Signs</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="BODY MEASUREMENT" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Body measurement</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.194" Name="DM Sex" DataType="string">
            <Description>
               <TranslatedText xml:lang="en">SEX</TranslatedText>
            </Description>
            <CodeListItem CodedValue="F" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">FEMALE</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="M" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">MALE</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.105" Name="EC_ECCAT" DataType="string" SASFormatName="ECCAT">
            <Description>
               <TranslatedText xml:lang="en">Category of Treatment</TranslatedText>
            </Description>
            <CodeListItem CodedValue="ADMINISTRATION OF TRIAL PRODUCT" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Administration of trial product</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.99" Name="EC_ECMOOD" DataType="string" SASFormatName="ECMOOD">
            <Description>
               <TranslatedText xml:lang="en">Mood</TranslatedText>
            </Description>
            <CodeListItem CodedValue="SCHEDULED" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Scheduled</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="PERFORMED" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Performed</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.107" Name="Yes" DataType="string">
            <Description>
               <TranslatedText xml:lang="en">NY</TranslatedText>
            </Description>
            <CodeListItem CodedValue="Y" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Yes</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.106" Name="EC_ECTRT&lt;IMP1&gt;" DataType="string" SASFormatName="ECTRT">
            <Description>
               <TranslatedText xml:lang="en">Name of Treatment</TranslatedText>
            </Description>
            <CodeListItem CodedValue="&lt;IMP 1&gt;" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">&lt;Investigational medicinal product 1&gt;</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="&lt;IMP 2&gt;" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">&lt;Investigational medicinal product 2&gt;</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="&lt;IMP 3&gt;" Rank="3.00">
               <Decode>
                  <TranslatedText xml:lang="en">&lt;Investigational medicinal product 3&gt;</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.100" Name="EC_dose_form" DataType="string" SASFormatName="ECDOSFRM">
            <Description>
               <TranslatedText xml:lang="en">FRM</TranslatedText>
            </Description>
            <CodeListItem CodedValue="TABLET" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Tablet</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="INJECTION" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Injection</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.98" Name="EC_type_of_treatment" DataType="string">
            <Description>
               <TranslatedText xml:lang="en">TREATMENT TYPE</TranslatedText>
            </Description>
            <CodeListItem CodedValue="PRE-PROPHYLAXIS REGIMEN" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Pre-prophylaxis dose</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="SCHEDULED PREVENTIVE TREATMENT" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Trial scheduled prophylaxis dose</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="PHYSICAL ACTIVITY" Rank="3.00">
               <Decode>
                  <TranslatedText xml:lang="en">Upcoming physical activity</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="OTHER PREVENTIVE TREATMENT" Rank="4.00">
               <Decode>
                  <TranslatedText xml:lang="en">Other preventive treatment</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="TREATMENT OF BLEED" Rank="5.00">
               <Decode>
                  <TranslatedText xml:lang="en">Treatment of bleeding episode</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="SURGERY" Rank="6.00">
               <Decode>
                  <TranslatedText xml:lang="en">Surgery</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.101" Name="EC_route" DataType="string" SASFormatName="ECROUTE">
            <Description>
               <TranslatedText xml:lang="en">ROUTE</TranslatedText>
            </Description>
            <CodeListItem CodedValue="SUBCUTANEOUS" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Subcutaneous</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="ORAL" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Oral</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.102" Name="EC_laterality" DataType="string" SASFormatName="ECLAT">
            <Description>
               <TranslatedText xml:lang="en">LAT</TranslatedText>
            </Description>
            <CodeListItem CodedValue="RIGHT" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Right</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="LEFT" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Left</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>

         <CodeList OID="CL.103" Name="EC_injection_site" DataType="string" SASFormatName="ECLOC">
            <Description>
               <TranslatedText xml:lang="en">LOC</TranslatedText>
            </Description>
            <CodeListItem CodedValue="UPPER ARM" Rank="1.00">
               <Decode>
                  <TranslatedText xml:lang="en">Upper arm (arm)</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="THIGH" Rank="2.00">
               <Decode>
                  <TranslatedText xml:lang="en">Thigh</TranslatedText>
               </Decode>
            </CodeListItem>
            <CodeListItem CodedValue="ABDOMINAL SKIN" Rank="3.00">
               <Decode>
                  <TranslatedText xml:lang="en">Stomach (abdominal skin)</TranslatedText>
               </Decode>
            </CodeListItem>
         </CodeList>



         <MethodDef OID="M.2" Name="BMEA_03_GD_BMI" Type="Computation">
            <Description>
               <TranslatedText xml:lang="en">Calculation of BMI based on height and weight</TranslatedText>
            </Description>
            <FormalExpression Context="Global derivation: BMEA_03_GD. FH standard calculation used."><![CDATA[var HEIGHT_FORM_STUDY_EVENT = 'VISIT 1'; var HEIGHT_FORM_NAME = 'Body Measurements (with BMI)' var bmi = null; var fixedNum = itemJson.item.significantDigits + 1; var weight = findFirstItemValueByName(formJson, 'VS_weight_VSTESTCD-VSORRES'); // update Study Event and Form Name as needed to look up previously-collected data var heightForm = findFormData(HEIGHT_FORM_STUDY_EVENT, HEIGHT_FORM_NAME); var height = findFirstItemValueByName(heightForm[0],'VS_height_VSTESTCD-VSORRES') if (height && weight) { //BMI = ( Weight in Kilograms / ( Height in Meters x Height in Meters ) ) //var heightMtr = (height / 100); bmi = (Math.round((weight / (height * height)) * 10) / 10); } return {'value': bmi.toPrecision(fixedNum +1), 'measurementUnitName': 'kg/m2'};]]></FormalExpression>
         </MethodDef>
      </MetaDataVersion>
   </Study>
</ODM>"""
clinspark_output = {
    "vendor_namespaces": [
        {
            "start_date": "2022-12-21T11:35:18.111000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_namespace1",
            "name": "nameOne",
            "library_name": "Sponsor",
            "prefix": "prefix",
            "url": "url1",
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "ClinTag",
                    "compatible_types": ["FormDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "odm_vendor_element1",
                    "name": "nameOne",
                    "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000002",
                    "name": "clinAttribute",
                    "data_type": "string",
                    "compatible_types": ["FormDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000004",
                    "name": "clinRefAttribute",
                    "data_type": "string",
                    "compatible_types": ["ItemGroupRef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "odm_vendor_attribute5",
                    "name": "nameFive",
                    "data_type": "string",
                    "compatible_types": ["NonCompatibleVendor"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "odm_vendor_attribute4",
                    "name": "nameFour",
                    "data_type": "string",
                    "compatible_types": [
                        "FormDef",
                        "ItemGroupDef",
                        "ItemDef",
                        "ItemGroupRef",
                        "ItemRef",
                    ],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "odm_vendor_attribute3",
                    "name": "nameThree",
                    "data_type": "string",
                    "compatible_types": [
                        "FormDef",
                        "ItemGroupDef",
                        "ItemDef",
                        "ItemGroupRef",
                        "ItemRef",
                    ],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "newClinAttribute",
                    "data_type": "string",
                    "compatible_types": ["ItemGroupDef"],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
            ],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
    "vendor_attributes": [
        {
            "start_date": "2022-12-21T11:36:30.962515+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000002",
            "name": "clinAttribute",
            "library_name": "Sponsor",
            "compatible_types": ["FormDef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:39.139846+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000004",
            "name": "clinRefAttribute",
            "library_name": "Sponsor",
            "compatible_types": ["ItemGroupRef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:38.235658+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000003",
            "name": "clinVendorElementAttribute",
            "library_name": "Sponsor",
            "compatible_types": [],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": None,
            "vendor_element": {
                "uid": "OdmVendorElement_000001",
                "name": "ClinTag",
                "compatible_types": ["FormDef"],
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:35:18.689000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_attribute5",
            "name": "nameFive",
            "library_name": "Sponsor",
            "compatible_types": [
                "NonCompatibleVendor",
            ],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:35:18.689000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "name": "nameFour",
            "change_description": "Approved version",
            "uid": "odm_vendor_attribute4",
            "library_name": "Sponsor",
            "compatible_types": [
                "FormDef",
                "ItemGroupDef",
                "ItemDef",
                "ItemGroupRef",
                "ItemRef",
            ],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:35:18.689000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_attribute3",
            "name": "nameThree",
            "library_name": "Sponsor",
            "compatible_types": [
                "FormDef",
                "ItemGroupDef",
                "ItemDef",
                "ItemGroupRef",
                "ItemRef",
            ],
            "data_type": "string",
            "value_regex": "^[a-zA-Z]+$",
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:31.234872+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorAttribute_000001",
            "name": "newClinAttribute",
            "library_name": "Sponsor",
            "compatible_types": ["ItemGroupDef"],
            "data_type": "string",
            "value_regex": None,
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_element": None,
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "vendor_elements": [
        {
            "start_date": "2022-12-21T11:36:37.975727+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmVendorElement_000001",
            "name": "ClinTag",
            "library_name": "Sponsor",
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "clinVendorElementAttribute",
                    "data_type": "string",
                    "compatible_types": [],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                }
            ],
            "compatible_types": ["FormDef"],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:35:18.375000+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "odm_vendor_element1",
            "name": "nameOne",
            "library_name": "Sponsor",
            "vendor_namespace": {
                "uid": "odm_vendor_namespace1",
                "name": "nameOne",
                "prefix": "prefix",
                "url": "url1",
                "status": "Final",
                "version": "1.0",
                "possible_actions": ["inactivate", "new_version"],
            },
            "vendor_attributes": [
                {
                    "uid": "odm_vendor_attribute1",
                    "name": "nameOne",
                    "data_type": "string",
                    "compatible_types": [],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
                {
                    "uid": "odm_vendor_attribute2",
                    "name": "nameTwo",
                    "data_type": "string",
                    "compatible_types": [],
                    "status": "Final",
                    "version": "1.0",
                    "possible_actions": ["inactivate", "new_version"],
                },
            ],
            "compatible_types": ["FormDef", "ItemGroupDef", "ItemDef"],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "study_events": [
        {
            "start_date": "2022-12-21T11:36:41.661594+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmStudyEvent_000001",
            "name": "Global Standards CRF Library",
            "library_name": "Sponsor",
            "oid": "Global Standards CRF Library",
            "effective_date": None,
            "retired_date": None,
            "description": None,
            "display_in_tree": True,
            "forms": [
                {
                    "uid": "OdmForm_000005",
                    "name": "Administration of <Investigational medicinal product> 1",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
                {
                    "uid": "OdmForm_000003",
                    "name": "Body Measurements (with BMI) 1",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
                {
                    "uid": "OdmForm_000002",
                    "name": "Demography 1",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
                {
                    "uid": "OdmForm_000001",
                    "name": "Informed Consent 1",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
                {
                    "uid": "OdmForm_000004",
                    "name": "Vital Signs (Single Measurement) 1",
                    "order_number": 999999,
                    "mandatory": "Yes",
                    "locked": "No",
                    "collection_exception_condition_oid": None,
                },
            ],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
    "forms": [
        {
            "start_date": "2022-12-21T11:36:40.909269+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000005",
            "name": "Administration of <Investigational medicinal product> 1",
            "library_name": "Sponsor",
            "oid": "F.38",
            "repeating": "Yes",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [],
            "aliases": [],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000005",
                    "oid": "IG.97",
                    "name": "Prescribed dose of <Investigational medicinal product> 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItemGroup_000006",
                    "oid": "IG.98",
                    "name": "Preparation for dosing 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItemGroup_000007",
                    "oid": "IG.99",
                    "name": "Administration of <Investigational medicinal product> 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItemGroup_000008",
                    "oid": "IG.267",
                    "name": "Post dose 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:40.362236+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000003",
            "name": "Body Measurements (with BMI) 1",
            "library_name": "Sponsor",
            "oid": "F.52",
            "repeating": "Yes",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000059",
                    "name": "Body Measurements form including weight, height and BMI calculation. Expected use for screening visit.",
                    "language": "ENG",
                    "description": "Body Measurements form including weight, height and BMI calculation. Expected use for screening visit.",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000003",
                    "oid": "IG.153",
                    "name": "Body Measurements 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                }
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:39.974375+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000002",
            "name": "Demography 1",
            "library_name": "Sponsor",
            "oid": "F.98",
            "repeating": "Yes",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [],
            "aliases": [],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000002",
                    "oid": "IG.262",
                    "name": "Demography 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                }
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:39.686457+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000001",
            "name": "Informed Consent 1",
            "library_name": "Sponsor",
            "oid": "F.47",
            "repeating": "No",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [],
            "aliases": [],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000001",
                    "oid": "IG.124",
                    "name": "Informed Consent 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {
                        "attributes": [
                            {
                                "uid": "OdmVendorAttribute_000004",
                                "name": "clinRefAttribute",
                                "data_type": "string",
                                "value_regex": None,
                                "value": "item grouop ref",
                                "vendor_namespace_uid": "odm_vendor_namespace1",
                            }
                        ]
                    },
                }
            ],
            "vendor_elements": [
                {
                    "uid": "OdmVendorElement_000001",
                    "name": "ClinTag",
                    "value": "vendor element value",
                }
            ],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000002",
                    "name": "clinAttribute",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "form value",
                    "vendor_namespace_uid": "odm_vendor_namespace1",
                }
            ],
            "vendor_element_attributes": [
                {
                    "uid": "OdmVendorAttribute_000003",
                    "name": "clinVendorElementAttribute",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "vendor element attribute value",
                    "vendor_element_uid": "OdmVendorElement_000001",
                }
            ],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:40.641659+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmForm_000004",
            "name": "Vital Signs (Single Measurement) 1",
            "library_name": "Sponsor",
            "oid": "F.37",
            "repeating": "Yes",
            "sdtm_version": "",
            "scope": None,
            "descriptions": [],
            "aliases": [],
            "activity_groups": [],
            "item_groups": [
                {
                    "uid": "OdmItemGroup_000004",
                    "oid": "IG.72",
                    "name": "Vital Signs 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                }
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "item_groups": [
        {
            "start_date": "2022-12-21T11:36:36.811353+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000007",
            "name": "Administration of <Investigational medicinal product> 1",
            "library_name": "Sponsor",
            "oid": "IG.99",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000058",
                    "name": "Exposure as Collected",
                    "language": "ENG",
                    "description": "Exposure as Collected",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000026",
                    "oid": "I.754",
                    "name": "EC_seq_no_ECREFID 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": "M.34",
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000027",
                    "oid": "I.471",
                    "name": "EC_ECCAT 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000028",
                    "oid": "I.473",
                    "name": "EC_ECMOOD 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000029",
                    "oid": "I.475",
                    "name": "EC_ECPRESP 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000030",
                    "oid": "I.474",
                    "name": "EC_<IMP>_ECTRT 1",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000039",
                    "oid": "I.565",
                    "name": "EC_adm_imp_ECOCCUR 1",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000040",
                    "oid": "I.578",
                    "name": "EC_specify_reason_ECREASOC 1",
                    "order_number": 7,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000041",
                    "oid": "I.576",
                    "name": "EC_type_of_treatment_ECSCAT 1",
                    "order_number": 8,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000042",
                    "oid": "I.580",
                    "name": "EC_bleed_no_ECXB 1",
                    "order_number": 9,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000043",
                    "oid": "I.581",
                    "name": "EC_surgery_no_ECPR 1",
                    "order_number": 10,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000044",
                    "oid": "I.582",
                    "name": "EC_start_datetime_ECSTDTC 1",
                    "order_number": 11,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000045",
                    "oid": "I.583",
                    "name": "EC_end_datetime_ECENDTC 1",
                    "order_number": 12,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000046",
                    "oid": "I.560",
                    "name": "EC_dose_ECDOSE 1",
                    "order_number": 13,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000033",
                    "oid": "I.561",
                    "name": "EC_dose_form_ECDOSFRM 1",
                    "order_number": 14,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000047",
                    "oid": "I.562",
                    "name": "EC_route_ECROUTE 1",
                    "order_number": 15,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000048",
                    "oid": "I.563",
                    "name": "EC_laterality_ECLAT 1",
                    "order_number": 16,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000049",
                    "oid": "I.564",
                    "name": "EC_inj_site_ECLOC 1",
                    "order_number": 17,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:34.902720+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000003",
            "name": "Body Measurements 1",
            "library_name": "Sponsor",
            "oid": "IG.153",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000055",
                    "name": "Body Measurements",
                    "language": "ENG",
                    "description": "Body Measurements",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000006",
                    "oid": "I.596",
                    "name": "VS_fasting_FASTING 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000007",
                    "oid": "I.597",
                    "name": "VS_VSCAT 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000008",
                    "oid": "I.637",
                    "name": "VS_date and time of exam_VSDTC 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000009",
                    "oid": "I.600",
                    "name": "VS_height_VSTESTCD-VSORRES 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000010",
                    "oid": "I.601",
                    "name": "VS_weight_VSTESTCD-VSORRES 1",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000011",
                    "oid": "I.621",
                    "name": "VS_BMI_VSORRES-VSTESTCD 1",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": "M.2",
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:34.391314+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000002",
            "name": "Demography 1",
            "library_name": "Sponsor",
            "oid": "IG.262",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000054",
                    "name": "Demographics",
                    "language": "ENG",
                    "description": "Demographics",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000012",
                    "oid": "I.1056",
                    "name": "DM_age_AGECOLL 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000013",
                    "oid": "I.1057",
                    "name": "DM Sex 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000014",
                    "oid": "I.1058",
                    "name": "DM Race - American Indian Or Alaska Native 1",
                    "order_number": 3,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000015",
                    "oid": "I.1059",
                    "name": "DM Race - Asian 1",
                    "order_number": 4,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000016",
                    "oid": "I.1060",
                    "name": "DM Race - Black Or African American 1",
                    "order_number": 5,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000017",
                    "oid": "I.1061",
                    "name": "DM Race - Native Hawaiian Or Other Pacific Islander 1",
                    "order_number": 6,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000018",
                    "oid": "I.1062",
                    "name": "DM Race - White 1",
                    "order_number": 7,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000019",
                    "oid": "I.1063",
                    "name": "DM Ethnicity 1",
                    "order_number": 8,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000020",
                    "oid": "I.1260",
                    "name": "DM_previous _subject_number_PREVSUBJ 1",
                    "order_number": 9,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:33.722232+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000001",
            "name": "Informed Consent 1",
            "library_name": "Sponsor",
            "oid": "IG.124",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000001",
                    "oid": "I.579",
                    "name": "DS_DSCAT 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000002",
                    "oid": "I.661",
                    "name": "DS_DSDECOD 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000003",
                    "oid": "I.566",
                    "name": "ICFVER_eS 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000004",
                    "oid": "I.567",
                    "name": "DS_inf_consent_DSSTDTC 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000005",
                    "oid": "I.568",
                    "name": "ICFNOTES_eS 1",
                    "order_number": 5,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [
                {
                    "uid": "OdmVendorAttribute_000001",
                    "name": "newClinAttribute",
                    "data_type": "string",
                    "value_regex": None,
                    "value": "item group attr",
                    "vendor_namespace_uid": "odm_vendor_namespace1",
                },
            ],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:37.032891+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000008",
            "name": "Post dose 1",
            "library_name": "Sponsor",
            "oid": "IG.267",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000050",
                    "oid": "I.589",
                    "name": "EC_admin_by_eS 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000051",
                    "oid": "I.590",
                    "name": "EC_check_by_eS 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000052",
                    "oid": "I.594",
                    "name": "EC_comment_eS 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:36.158563+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000006",
            "name": "Preparation for dosing 1",
            "library_name": "Sponsor",
            "oid": "IG.98",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000034",
                    "oid": "I.585",
                    "name": "EC_req_met_eS 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000035",
                    "oid": "I.586",
                    "name": "EC_morph_inj_site_eS 1",
                    "order_number": 2,
                    "mandatory": "No",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000036",
                    "oid": "I.588",
                    "name": "EC_dun_eS 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000037",
                    "oid": "I.592",
                    "name": "EC_no_inj_eS 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000038",
                    "oid": "I.593",
                    "name": "EC_volume_eS 1",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:35.847304+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000005",
            "name": "Prescribed dose of <Investigational medicinal product> 1",
            "library_name": "Sponsor",
            "oid": "IG.97",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000057",
                    "name": "Exposure as Collected",
                    "language": "ENG",
                    "description": "Exposure as Collected",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000026",
                    "oid": "I.754",
                    "name": "EC_seq_no_ECREFID 1",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": "M.34",
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000027",
                    "oid": "I.471",
                    "name": "EC_ECCAT 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000028",
                    "oid": "I.473",
                    "name": "EC_ECMOOD 1",
                    "order_number": 3,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000029",
                    "oid": "I.475",
                    "name": "EC_ECPRESP 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000030",
                    "oid": "I.474",
                    "name": "EC_<IMP>_ECTRT 1",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000031",
                    "oid": "I.595",
                    "name": "EC_datetime_prescription_ECSTDTC 1",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000032",
                    "oid": "I.559",
                    "name": "EC_prescribed_dose_ECDOSE 1",
                    "order_number": 7,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000033",
                    "oid": "I.561",
                    "name": "EC_dose_form_ECDOSFRM 1",
                    "order_number": 8,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:35.351984+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItemGroup_000004",
            "name": "Vital Signs 1",
            "library_name": "Sponsor",
            "oid": "IG.72",
            "repeating": "No",
            "is_reference_data": "No",
            "sas_dataset_name": "",
            "origin": "",
            "purpose": "Tabulation",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000056",
                    "name": "Vital Signs",
                    "language": "ENG",
                    "description": "Vital Signs",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "sdtm_domains": [],
            "activity_subgroups": [],
            "items": [
                {
                    "uid": "OdmItem_000021",
                    "oid": "I.406",
                    "name": "VS_VSCAT 2",
                    "order_number": 1,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000022",
                    "oid": "I.354",
                    "name": "VS_date of exam_VSDTC 1",
                    "order_number": 2,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000023",
                    "oid": "I.355",
                    "name": "VS_syst_blood_pres_ORRES_SYSBP 1",
                    "order_number": 4,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000024",
                    "oid": "I.356",
                    "name": "VS_diast_blood_pres_ORRES_DIABP 1",
                    "order_number": 5,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
                {
                    "uid": "OdmItem_000025",
                    "oid": "I.347",
                    "name": "VS_pulse_ORRES_PULSE 1",
                    "order_number": 6,
                    "mandatory": "Yes",
                    "key_sequence": "None",
                    "method_oid": None,
                    "imputation_method_oid": "None",
                    "role": "None",
                    "role_codelist_oid": "None",
                    "collection_exception_condition_oid": "",
                    "vendor": {"attributes": []},
                },
            ],
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "items": [
        {
            "start_date": "2022-12-21T11:36:15.992084+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000019",
            "name": "DM Ethnicity 1",
            "library_name": "Sponsor",
            "oid": "I.1063",
            "prompt": "",
            "datatype": "string",
            "length": 100,
            "significant_digits": None,
            "sas_field_name": "ETHNIC",
            "sds_var_name": "DM:ETHNIC",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000020",
                    "name": "Subject self-reported ethnicity",
                    "language": "ENG",
                    "description": "Ethnicity",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:14.306878+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000014",
            "name": "DM Race - American Indian Or Alaska Native 1",
            "library_name": "Sponsor",
            "oid": "I.1058",
            "prompt": "",
            "datatype": "boolean",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "RACE1",
            "sds_var_name": "DM:RACE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000015",
                    "name": "Subject self-reported race - American Indian Or Alaska Native",
                    "language": "ENG",
                    "description": "Race - American Indian Or Alaska Native",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:14.645699+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000015",
            "name": "DM Race - Asian 1",
            "library_name": "Sponsor",
            "oid": "I.1059",
            "prompt": "",
            "datatype": "boolean",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "RACE2",
            "sds_var_name": "DM:RACE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000016",
                    "name": "Subject self-reported race - Asian",
                    "language": "ENG",
                    "description": "Race - Asian",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:14.972105+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000016",
            "name": "DM Race - Black Or African American 1",
            "library_name": "Sponsor",
            "oid": "I.1060",
            "prompt": "",
            "datatype": "boolean",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "RACE3",
            "sds_var_name": "DM:RACE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000017",
                    "name": "Subject self-reported race - Black or African American",
                    "language": "ENG",
                    "description": "Race - Black Or African American",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:15.340405+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000017",
            "name": "DM Race - Native Hawaiian Or Other Pacific Islander 1",
            "library_name": "Sponsor",
            "oid": "I.1061",
            "prompt": "",
            "datatype": "boolean",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "RACE4",
            "sds_var_name": "DM:RACE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000018",
                    "name": "Subject self-reported race - Native Hawaiian or Other Pacific Islander",
                    "language": "ENG",
                    "description": "Race - Native Hawaiian Or Other Pacific Islander",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:15.667687+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000018",
            "name": "DM Race - White 1",
            "library_name": "Sponsor",
            "oid": "I.1062",
            "prompt": "",
            "datatype": "boolean",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "RACE5",
            "sds_var_name": "DM:RACE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000019",
                    "name": "Subject self-reported race - White",
                    "language": "ENG",
                    "description": "Race - White",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:13.978468+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000013",
            "name": "DM Sex 1",
            "library_name": "Sponsor",
            "oid": "I.1057",
            "prompt": "",
            "datatype": "string",
            "length": 100,
            "significant_digits": None,
            "sas_field_name": "SEX",
            "sds_var_name": "DM:SEX",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000014",
                    "name": "Sex",
                    "language": "ENG",
                    "description": "Sex",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000005",
                "name": "DM Sex",
                "submission_value": "SEX",
                "preferred_term": "DM Sex",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000017",
                    "name": "FEMALE",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000018",
                    "name": "MALE",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:13.457466+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000012",
            "name": "DM_age_AGECOLL 1",
            "library_name": "Sponsor",
            "oid": "I.1056",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "AGECOLL",
            "sds_var_name": "DM:AGE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000013",
                    "name": "Age",
                    "language": "ENG",
                    "description": "Age",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:16.325406+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000020",
            "name": "DM_previous _subject_number_PREVSUBJ 1",
            "library_name": "Sponsor",
            "oid": "I.1260",
            "prompt": "",
            "datatype": "integer",
            "length": 6,
            "significant_digits": None,
            "sas_field_name": "PREVSUBJ",
            "sds_var_name": "DM:PREVUBJ",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000021",
                    "name": "Previous Subject No.",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:07.412780+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000001",
            "name": "DS_DSCAT 1",
            "library_name": "Sponsor",
            "oid": "I.579",
            "prompt": "",
            "datatype": "text",
            "length": 18,
            "significant_digits": None,
            "sas_field_name": "DSCAT",
            "sds_var_name": "DS:DSCAT",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000002",
                    "name": "DSCAT",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000002",
                "name": "DS_DSCAT",
                "submission_value": "DSCAT",
                "preferred_term": "DS_DSCAT",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000003",
                    "name": "Disposition event",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000004",
                    "name": "Protocol milestone",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000005",
                    "name": "Other event",
                    "mandatory": True,
                    "order": 3,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:08.346051+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000002",
            "name": "DS_DSDECOD 1",
            "library_name": "Sponsor",
            "oid": "I.661",
            "prompt": "",
            "datatype": "text",
            "length": 43,
            "significant_digits": None,
            "sas_field_name": "DSDECOD",
            "sds_var_name": "DS:DSDECOD",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000003",
                    "name": "DSDECOD",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000003",
                "name": "DS_DSTERM",
                "submission_value": "NCOMPLT",
                "preferred_term": "DS_DSTERM",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000006",
                    "name": "First date on trial product",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000007",
                    "name": "Last date on trial product",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000008",
                    "name": "Treatment discontinuation",
                    "mandatory": True,
                    "order": 3,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000009",
                    "name": "Treatment unblinded",
                    "mandatory": True,
                    "order": 4,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000010",
                    "name": "Informed consent obtained",
                    "mandatory": True,
                    "order": 5,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000011",
                    "name": "Eligibility criteria met",
                    "mandatory": True,
                    "order": 6,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000012",
                    "name": "Randomized",
                    "mandatory": True,
                    "order": 7,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000013",
                    "name": "Future research biosample consent obtained",
                    "mandatory": True,
                    "order": 8,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000014",
                    "name": "Future research biosample consent withdrawn",
                    "mandatory": True,
                    "order": 9,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:09.089752+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000004",
            "name": "DS_inf_consent_DSSTDTC 1",
            "library_name": "Sponsor",
            "oid": "I.567",
            "prompt": "",
            "datatype": "datetime",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "DSSTDTC",
            "sds_var_name": "DS:DSSTDTC",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000005",
                    "name": "Date and time informed consent obtained",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:20.684162+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000030",
            "name": "EC_<IMP>_ECTRT 1",
            "library_name": "Sponsor",
            "oid": "I.474",
            "prompt": "",
            "datatype": "string",
            "length": 7,
            "significant_digits": None,
            "sas_field_name": "ECTRT",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000031",
                    "name": "<Investigational medicinal product>",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000008",
                "name": "EC_ECTRT<IMP1>",
                "submission_value": "Name of Treatment",
                "preferred_term": "EC_ECTRT<IMP1>",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000022",
                    "name": "<Investigational medicinal product 1>",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000023",
                    "name": "<Investigational medicinal product 2>",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000024",
                    "name": "<Investigational medicinal product 3>",
                    "mandatory": True,
                    "order": 3,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:19.123838+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000027",
            "name": "EC_ECCAT 1",
            "library_name": "Sponsor",
            "oid": "I.471",
            "prompt": "",
            "datatype": "string",
            "length": 31,
            "significant_digits": None,
            "sas_field_name": "ECCAT",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000028",
                    "name": "ECCAT",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000006",
                "name": "EC_ECCAT",
                "submission_value": "Category of Treatment",
                "preferred_term": "EC_ECCAT",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000019",
                    "name": "Administration of trial product",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                }
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:19.630002+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000028",
            "name": "EC_ECMOOD 1",
            "library_name": "Sponsor",
            "oid": "I.473",
            "prompt": "",
            "datatype": "string",
            "length": 9,
            "significant_digits": None,
            "sas_field_name": "ECMOOD",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000029",
                    "name": "ECMOOD",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000007",
                "name": "EC_ECMOOD",
                "submission_value": "Mood",
                "preferred_term": "EC_ECMOOD",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000020",
                    "name": "Scheduled",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000021",
                    "name": "Performed",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:20.104491+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000029",
            "name": "EC_ECPRESP 1",
            "library_name": "Sponsor",
            "oid": "I.475",
            "prompt": "",
            "datatype": "string",
            "length": 1,
            "significant_digits": None,
            "sas_field_name": "ECPRESP",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000030",
                    "name": "ECPRESP",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000001",
                "name": "No Yes Response",
                "submission_value": "NY",
                "preferred_term": "No Yes Response",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000001",
                    "name": "Yes",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                }
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:24.341147+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000039",
            "name": "EC_adm_imp_ECOCCUR 1",
            "library_name": "Sponsor",
            "oid": "I.565",
            "prompt": "",
            "datatype": "string",
            "length": 1,
            "significant_digits": None,
            "sas_field_name": "ECOCCUR",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000040",
                    "name": "Has the investigational medicinal product been administered to the subject?",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000001",
                "name": "No Yes Response",
                "submission_value": "NY",
                "preferred_term": "No Yes Response",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000001",
                    "name": "Yes",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000002",
                    "name": "No",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:28.935309+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000050",
            "name": "EC_admin_by_eS 1",
            "library_name": "Sponsor",
            "oid": "I.589",
            "prompt": "",
            "datatype": "text",
            "length": 4,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000051",
                    "name": "Administered by",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:25.682690+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000042",
            "name": "EC_bleed_no_ECXB 1",
            "library_name": "Sponsor",
            "oid": "I.580",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "ECXB",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000043",
                    "name": "Bleeding episode no.",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:29.260287+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000051",
            "name": "EC_check_by_eS 1",
            "library_name": "Sponsor",
            "oid": "I.590",
            "prompt": "",
            "datatype": "text",
            "length": 4,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000052",
                    "name": "Checked by",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:29.592149+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000052",
            "name": "EC_comment_eS 1",
            "library_name": "Sponsor",
            "oid": "I.594",
            "prompt": "",
            "datatype": "text",
            "length": 200,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000053",
                    "name": "Comment",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:21.004983+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000031",
            "name": "EC_datetime_prescription_ECSTDTC 1",
            "library_name": "Sponsor",
            "oid": "I.595",
            "prompt": "",
            "datatype": "partialDatetime",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "ECSTDTC",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000032",
                    "name": "Start date and time of prescription",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:27.026955+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000046",
            "name": "EC_dose_ECDOSE 1",
            "library_name": "Sponsor",
            "oid": "I.560",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "ECDOSE",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000047",
                    "name": "Actual Dose",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:21.964398+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000033",
            "name": "EC_dose_form_ECDOSFRM 1",
            "library_name": "Sponsor",
            "oid": "I.561",
            "prompt": "",
            "datatype": "string",
            "length": 9,
            "significant_digits": None,
            "sas_field_name": "ECDOSFRM",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000034",
                    "name": "Dose form",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000009",
                "name": "EC_dose_form",
                "submission_value": "FRM",
                "preferred_term": "EC_dose_form",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000025",
                    "name": "Tablet",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000026",
                    "name": "Injection",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:23.118066+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000036",
            "name": "EC_dun_eS 1",
            "library_name": "Sponsor",
            "oid": "I.588",
            "prompt": "",
            "datatype": "integer",
            "length": 6,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000037",
                    "name": "DUN (Dispensing Unit No.)",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:26.703316+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000045",
            "name": "EC_end_datetime_ECENDTC 1",
            "library_name": "Sponsor",
            "oid": "I.583",
            "prompt": "",
            "datatype": "datetime",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "ECENDTC",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000046",
                    "name": "End date and time of administration",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:28.602920+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000049",
            "name": "EC_inj_site_ECLOC 1",
            "library_name": "Sponsor",
            "oid": "I.564",
            "prompt": "",
            "datatype": "string",
            "length": 14,
            "significant_digits": None,
            "sas_field_name": "ECLOC",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000050",
                    "name": "Injection site",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000013",
                "name": "EC_injection_site",
                "submission_value": "LOC",
                "preferred_term": "EC_injection_site",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000037",
                    "name": "Upper arm (arm)",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000038",
                    "name": "Thigh",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000039",
                    "name": "Stomach (abdominal skin)",
                    "mandatory": True,
                    "order": 3,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:28.064261+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000048",
            "name": "EC_laterality_ECLAT 1",
            "library_name": "Sponsor",
            "oid": "I.563",
            "prompt": "",
            "datatype": "string",
            "length": 5,
            "significant_digits": None,
            "sas_field_name": "ECLAT",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000049",
                    "name": "Laterality",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000012",
                "name": "EC_laterality",
                "submission_value": "LAT",
                "preferred_term": "EC_laterality",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000035",
                    "name": "Right",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000036",
                    "name": "Left",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:22.797283+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000035",
            "name": "EC_morph_inj_site_eS 1",
            "library_name": "Sponsor",
            "oid": "I.586",
            "prompt": "",
            "datatype": "text",
            "length": 200,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000036",
                    "name": "Morphology of injection site",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:23.436791+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000037",
            "name": "EC_no_inj_eS 1",
            "library_name": "Sponsor",
            "oid": "I.592",
            "prompt": "",
            "datatype": "integer",
            "length": 1,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000038",
                    "name": "Number of injections",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:21.328907+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000032",
            "name": "EC_prescribed_dose_ECDOSE 1",
            "library_name": "Sponsor",
            "oid": "I.559",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "ECDOSE",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000033",
                    "name": "Prescribed dose",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:22.470927+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000034",
            "name": "EC_req_met_eS 1",
            "library_name": "Sponsor",
            "oid": "I.585",
            "prompt": "",
            "datatype": "string",
            "length": 1,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000035",
                    "name": "Requirements for dosing met?",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000001",
                "name": "No Yes Response",
                "submission_value": "NY",
                "preferred_term": "No Yes Response",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000001",
                    "name": "Yes",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000002",
                    "name": "No",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:27.541401+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000047",
            "name": "EC_route_ECROUTE 1",
            "library_name": "Sponsor",
            "oid": "I.562",
            "prompt": "",
            "datatype": "string",
            "length": 12,
            "significant_digits": None,
            "sas_field_name": "ECROUTE",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000048",
                    "name": "Route",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000011",
                "name": "EC_route",
                "submission_value": "ROUTE",
                "preferred_term": "EC_route",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000033",
                    "name": "Subcutaneous",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000034",
                    "name": "Oral",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:18.651232+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000026",
            "name": "EC_seq_no_ECREFID 1",
            "library_name": "Sponsor",
            "oid": "I.754",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "ECREFID",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000027",
                    "name": "Seq. no.",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:24.686862+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000040",
            "name": "EC_specify_reason_ECREASOC 1",
            "library_name": "Sponsor",
            "oid": "I.578",
            "prompt": "",
            "datatype": "text",
            "length": 200,
            "significant_digits": None,
            "sas_field_name": "ECREASOC",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000041",
                    "name": "Specify reason",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:26.340779+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000044",
            "name": "EC_start_datetime_ECSTDTC 1",
            "library_name": "Sponsor",
            "oid": "I.582",
            "prompt": "",
            "datatype": "datetime",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "ECSTDTC",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000045",
                    "name": "Start date and time of administration",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:26.004203+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000043",
            "name": "EC_surgery_no_ECPR 1",
            "library_name": "Sponsor",
            "oid": "I.581",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "ECPR",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000044",
                    "name": "Surgery no.",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:25.345007+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000041",
            "name": "EC_type_of_treatment_ECSCAT 1",
            "library_name": "Sponsor",
            "oid": "I.576",
            "prompt": "",
            "datatype": "string",
            "length": 30,
            "significant_digits": None,
            "sas_field_name": "ECSCAT",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000042",
                    "name": "Type of treatment",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000010",
                "name": "EC_type_of_treatment",
                "submission_value": "TREATMENT TYPE",
                "preferred_term": "EC_type_of_treatment",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000027",
                    "name": "Pre-prophylaxis dose",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000028",
                    "name": "Trial scheduled prophylaxis dose",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000029",
                    "name": "Upcoming physical activity",
                    "mandatory": True,
                    "order": 3,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000030",
                    "name": "Other preventive treatment",
                    "mandatory": True,
                    "order": 4,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000031",
                    "name": "Treatment of bleeding episode",
                    "mandatory": True,
                    "order": 5,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000032",
                    "name": "Surgery",
                    "mandatory": True,
                    "order": 6,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:23.840443+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000038",
            "name": "EC_volume_eS 1",
            "library_name": "Sponsor",
            "oid": "I.593",
            "prompt": "",
            "datatype": "float",
            "length": 4,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000039",
                    "name": "Volume administered",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:09.526382+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000005",
            "name": "ICFNOTES_eS 1",
            "library_name": "Sponsor",
            "oid": "I.568",
            "prompt": "",
            "datatype": "text",
            "length": 999,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000006",
                    "name": "ICF Notes",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:08.690435+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000003",
            "name": "ICFVER_eS 1",
            "library_name": "Sponsor",
            "oid": "I.566",
            "prompt": "",
            "datatype": "string",
            "length": 200,
            "significant_digits": None,
            "sas_field_name": "",
            "sds_var_name": "DS:ICFVER",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000004",
                    "name": "ICF Version",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:12.992778+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000011",
            "name": "VS_BMI_VSORRES-VSTESTCD 1",
            "library_name": "Sponsor",
            "oid": "I.621",
            "prompt": "",
            "datatype": "float",
            "length": 4,
            "significant_digits": None,
            "sas_field_name": "VSTESTCD",
            "sds_var_name": "BMI",
            "origin": "Protocol",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000012",
                    "name": "BMI",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:10.711772+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000007",
            "name": "VS_VSCAT 1",
            "library_name": "Sponsor",
            "oid": "I.597",
            "prompt": "",
            "datatype": "text",
            "length": 16,
            "significant_digits": None,
            "sas_field_name": "VSCAT",
            "sds_var_name": "VS:VSCAT",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000008",
                    "name": "VSCAT",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000004",
                "name": "VS_VSCAT",
                "submission_value": "VSCAT",
                "preferred_term": "VS_VSCAT",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000015",
                    "name": "Vital Signs",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000016",
                    "name": "Body measurement",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:16.852810+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000021",
            "name": "VS_VSCAT 2",
            "library_name": "Sponsor",
            "oid": "I.406",
            "prompt": "",
            "datatype": "text",
            "length": 16,
            "significant_digits": None,
            "sas_field_name": "VSCAT",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000022",
                    "name": "VSCAT",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000004",
                "name": "VS_VSCAT",
                "submission_value": "VSCAT",
                "preferred_term": "VS_VSCAT",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000015",
                    "name": "Vital Signs",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000016",
                    "name": "Body measurement",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:11.049901+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000008",
            "name": "VS_date and time of exam_VSDTC 1",
            "library_name": "Sponsor",
            "oid": "I.637",
            "prompt": "",
            "datatype": "datetime",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "VSDTC",
            "sds_var_name": "VS:VSDTC",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000009",
                    "name": "Date and time of examination",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:17.180503+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000022",
            "name": "VS_date of exam_VSDTC 1",
            "library_name": "Sponsor",
            "oid": "I.354",
            "prompt": "",
            "datatype": "date",
            "length": None,
            "significant_digits": None,
            "sas_field_name": "VSDTC",
            "sds_var_name": "",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000023",
                    "name": "Date of examination",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:18.007900+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000024",
            "name": "VS_diast_blood_pres_ORRES_DIABP 1",
            "library_name": "Sponsor",
            "oid": "I.356",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "VSTESTCD",
            "sds_var_name": "DIABP",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000025",
                    "name": "Diastolic blood pressure",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:10.104927+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000006",
            "name": "VS_fasting_FASTING 1",
            "library_name": "Sponsor",
            "oid": "I.596",
            "prompt": "",
            "datatype": "string",
            "length": 1,
            "significant_digits": None,
            "sas_field_name": "FASTING",
            "sds_var_name": "VS:FASTING",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000007",
                    "name": "Was the subject fasting when the body measurement was done?",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": {
                "uid": "CTCodelist_000001",
                "name": "No Yes Response",
                "submission_value": "NY",
                "preferred_term": "No Yes Response",
            },
            "terms": [
                {
                    "term_uid": "CTTerm_000001",
                    "name": "Yes",
                    "mandatory": True,
                    "order": 1,
                    "display_text": None,
                    "version": "1.0",
                },
                {
                    "term_uid": "CTTerm_000002",
                    "name": "No",
                    "mandatory": True,
                    "order": 2,
                    "display_text": None,
                    "version": "1.0",
                },
            ],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:11.954279+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000009",
            "name": "VS_height_VSTESTCD-VSORRES 1",
            "library_name": "Sponsor",
            "oid": "I.600",
            "prompt": "",
            "datatype": "float",
            "length": 1,
            "significant_digits": None,
            "sas_field_name": "VSTESTCD",
            "sds_var_name": "HEIGHT",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000010",
                    "name": "Height",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:18.329739+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000025",
            "name": "VS_pulse_ORRES_PULSE 1",
            "library_name": "Sponsor",
            "oid": "I.347",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "VSTESTCD",
            "sds_var_name": "PULSE",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000026",
                    "name": "Pulse",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:17.609186+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000023",
            "name": "VS_syst_blood_pres_ORRES_SYSBP 1",
            "library_name": "Sponsor",
            "oid": "I.355",
            "prompt": "",
            "datatype": "integer",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "VSTESTCD",
            "sds_var_name": "SYSBP",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000024",
                    "name": "Systolic blood pressure",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
        {
            "start_date": "2022-12-21T11:36:12.456401+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmItem_000010",
            "name": "VS_weight_VSTESTCD-VSORRES 1",
            "library_name": "Sponsor",
            "oid": "I.601",
            "prompt": "",
            "datatype": "float",
            "length": 3,
            "significant_digits": None,
            "sas_field_name": "VSTESTCD",
            "sds_var_name": "WEIGHT",
            "origin": "CRF",
            "comment": None,
            "descriptions": [
                {
                    "uid": "OdmDescription_000011",
                    "name": "Body weight",
                    "language": "ENG",
                    "description": "Please update this description",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "unit_definitions": [
                {
                    "uid": "unit_definition_root1",
                    "name": "name1",
                    "mandatory": True,
                    "order": 999999,
                    "ucum": {
                        "term_uid": "term_root1_uid",
                        "name": "name1",
                        "dictionary_id": "dictionary_id1",
                    },
                    "ct_units": [{"term_uid": "C25532_name1", "name": "name1"}],
                }
            ],
            "codelist": None,
            "terms": [],
            "activity": None,
            "vendor_elements": [],
            "vendor_attributes": [],
            "vendor_element_attributes": [],
            "possible_actions": ["inactivate", "new_version"],
        },
    ],
    "conditions": [],
    "methods": [
        {
            "start_date": "2022-12-21T11:36:05.487419+00:00",
            "end_date": None,
            "status": "Final",
            "version": "1.0",
            "author_username": "unknown-user@example.com",
            "change_description": "Approved version",
            "uid": "OdmMethod_000001",
            "name": "BMEA_03_GD_BMI",
            "library_name": "Sponsor",
            "oid": "M.2",
            "method_type": "BMEA_03_GD_BMI",
            "formal_expressions": [
                {
                    "uid": "OdmFormalExpression_000001",
                    "context": "Global derivation: BMEA_03_GD. FH standard calculation used.",
                    "expression": "var HEIGHT_FORM_STUDY_EVENT = 'VISIT 1'; var HEIGHT_FORM_NAME = 'Body Measurements (with BMI)' var bmi = null; var fixedNum = itemJson.item.significantDigits + 1; var weight = findFirstItemValueByName(formJson, 'VS_weight_VSTESTCD-VSORRES'); // update Study Event and Form Name as needed to look up previously-collected data var heightForm = findFormData(HEIGHT_FORM_STUDY_EVENT, HEIGHT_FORM_NAME); var height = findFirstItemValueByName(heightForm[0],'VS_height_VSTESTCD-VSORRES') if (height && weight) { //BMI = ( Weight in Kilograms / ( Height in Meters x Height in Meters ) ) //var heightMtr = (height / 100); bmi = (Math.round((weight / (height * height)) * 10) / 10); } return {'value': bmi.toPrecision(fixedNum +1), 'measurementUnitName': 'kg/m2'};",
                    "version": "1.0",
                }
            ],
            "descriptions": [
                {
                    "uid": "OdmDescription_000001",
                    "name": "Calculation of BMI based on height and weight",
                    "language": "ENG",
                    "description": "Calculation of BMI based on height and weight",
                    "instruction": "Please update this instruction",
                    "sponsor_instruction": "Please update this sponsor instruction",
                    "version": "1.0",
                }
            ],
            "aliases": [],
            "possible_actions": ["inactivate", "new_version"],
        }
    ],
}
