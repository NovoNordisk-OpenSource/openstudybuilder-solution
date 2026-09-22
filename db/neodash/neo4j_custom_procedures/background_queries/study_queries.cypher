:param  neodash_studya => 'CDISC DEV-0';
:param  neodash_studyb => 'CDISC DEV-0001';
:param  neodash_versiondate_studya =>'2023-10-12T04:32:32';
:param  neodash_versiondate_studyb =>'2023-10-12T04:36:59';
:param  neodash_wrap_limit => 60

:param  neodash_studya => 'CDISC DEV-0';
:param  neodash_studyb => 'CDISC DEV-0';
:param  neodash_versiondate_studya =>'2024-02-12T07:05:34';
:param  neodash_versiondate_studyb =>'2024-02-12T06:34:08';
:param  neodash_wrap_limit => 60;
:param  neodash_wrap_limit_1 => 60;
:param  neodash_wrap_limit_2 => 60;
:param  neodash_wrap_limit_3 => 60

:param  neodash_studya => 1146415;
:param  neodash_studyb => 1146414;
:param  neodash_wrap_limit => 60;
:param  neodash_wrap_limit_1 => 60;
:param  neodash_wrap_limit_2 => 60;
:param  neodash_wrap_limit_3 => 60

//Show selected by id
return 'Base: '+toString($neodash_studya)+'\n Comp:'+toString($neodash_studyb)



//project selector
MATCH (p:Project)-[:HAS_FIELD]->(:StudyProjectField)<-[:HAS_PROJECT]-(s:StudyValue)
WHERE p.project_number CONTAINS toLower($input) 
RETURN DISTINCT p.`project_number` as value,  p.`project_number` as display ORDER BY size(toString(value)) ASC LIMIT 10

//study list
CALL apoc.when(size($neodash_project)=0,"match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, s.study_id_prefix+'-'+s.study_number as trialid
with s, trialid 
match (sr:StudyRoot)-[r0:HAS_VERSION]->(s)
optional match(s)<-[r:AFTER]-(sact:StudyAction)
with distinct trialid,sr.uid as StudyRoot, collect(r0.status) as statuses ,collect(r0.version) as versions, sact.date as date order by StudyRoot, sact.date
with trialid, split(apoc.temporal.format(date, 'iso_local_date_time'),'.')[0] as Date, case when 'LOCKED' in statuses then 'LOCKED' else 'DRAFT' END as Status,
apoc.text.join(apoc.coll.toSet(versions),'') as Version 
return trialid as TrialID, Date, Version, Status",
"match(p:Project)-[:HAS_FIELD]->(:StudyProjectField)<-[:HAS_PROJECT]-(s:StudyValue) 
where p.project_number in $a
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, s.study_id_prefix+'-'+s.study_number as trialid
with s, trialid
match (sr:StudyRoot)-[r0:HAS_VERSION]->(s)
optional match(s)<-[r:AFTER]-(sact:StudyAction)
with distinct trialid,sr.uid as StudyRoot, collect(r0.status) as statuses ,collect(r0.version) as versions, sact.date as date order by StudyRoot, sact.date
with trialid, split(apoc.temporal.format(date, 'iso_local_date_time'),'.')[0] as Date, case when 'LOCKED' in statuses then 'LOCKED' else 'DRAFT' END as Status,
apoc.text.join(apoc.coll.toSet(versions),'') as Version 
return trialid as TrialID, Date, Version, Status",{a:$neodash_project}) YIELD value 
RETURN  value.TrialID as `Trial ID`,
value.Date as Date,
value.Version as Version,
value.Status as Status

//select studyA - custom query for neodash_studya and same for neodash_studyb
MATCH (p:Project)-[:HAS_FIELD]->(:StudyProjectField)<-[:HAS_PROJECT]-(s:StudyValue) where p.project_number in $neodash_project
MATCH (sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
WITH s.study_id_prefix+'-'+s.study_number as trialid
WITH trialid WHERE toLower(toString(trialid)) CONTAINS toLower($input) 
RETURN DISTINCT `trialid` as value,  `trialid` as display ORDER BY size(toString(value)) ASC LIMIT 100

// Select version for studyA - custom query for neodash_versiondate_studya
MATCH (sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
WITH r0, s.study_id_prefix+'-'+s.study_number as trialid
WITH r0, trialid WHERE trialid=$neodash_studya and toLower(toString(r0.`start_date`)) CONTAINS toLower($input) 
RETURN DISTINCT split(apoc.temporal.format(r0.`start_date`, "iso_local_date_time"),'.')[0] as value,   split(apoc.temporal.format(r0.`start_date`, "iso_local_date_time"),'.')[0] as display ORDER BY size(toString(value)) ASC LIMIT 10

// select version for studyb - custom query for noedash_versiondate_studyb
MATCH (sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue) 
WITH r0, s.study_id_prefix+'-'+s.study_number as trialid
WITH r0, trialid WHERE trialid=$neodash_studyb and not r0.start_date in [datetime($neodash_versiondate_studya)] 
WITH r0, trialid WHERE toLower(toString(r0.`start_date`)) CONTAINS toLower($input) 
RETURN DISTINCT split(apoc.temporal.format(r0.`start_date`, "iso_local_date_time"),'.')[0] as value,  split(apoc.temporal.format(r0.`start_date`, "iso_local_date_time"),'.')[0] as display ORDER BY size(toString(value)) ASC LIMIT 10


//Study field comparison table
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, s.study_id_prefix+'-'+s.study_number as trialid, 
split(apoc.temporal.format(r0.start_date, "iso_local_date_time"),'.')[0] as start_date
with start_date, s, trialid where trialid in[$neodash_studya, $neodash_studyb] 
and datetime(start_date) in [datetime($neodash_versiondate_studya),datetime($neodash_versiondate_studyb)]
match (s)-[r1]->(txt:StudyField) where txt.field_name is not null
with distinct start_date, trialid, txt.field_name as field ,txt.value as value, CASE WHEN not $neodash_wrap_limit ='' THEN $neodash_wrap_limit ELSE 50 END as wrap_limit
WITH CASE WHEN trialid=$neodash_studya and datetime(start_date)=datetime($neodash_versiondate_studya) THEN 'Base' ELSE 'Compare' END as study, field, value, 
CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(value)='STRING' THEN apoc.text.indexesOf(value, ' ')  ELSE null END as space_pos1
WITH study,field, space_pos1, CASE wrap_limit WHEN '0' THEN [0] ELSE[x in space_pos1 | x/wrap_limit ] END as div, value
WITH study,field, space_pos1, div, CASE WHEN size(div) >0 THEN apoc.coll.toSet(div) ELSE [-1] END as freq, value
WITH study,field,space_pos1, div, freq, value
UNWIND freq as f
WITH study,field,space_pos1, div, apoc.coll.runningTotal(collect(apoc.coll.occurrences(div,f))) as occ, value
WITH study,field,space_pos1,value, [
    x in RANGE(0,size(occ)-1) | CASE x WHEN 0 THEN [x,occ[x]-1] ELSE [occ[x-1]-1,occ[x]-1] END
    ] as pair, occ
    with study,field, space_pos1, value, occ,[x in pair where x[1] is not null] as pair
WITH study,field, space_pos1, value, pair, occ,[x in pair | CASE x[0] WHEN 0 THEN [0,space_pos1[x[1]]] ELSE CASE x[0] WHEN pair[size(pair)-1][0] THEN [space_pos1[x[0]],size(value)] ELSE [space_pos1[x[0]],space_pos1[x[1]]-space_pos1[x[0]]] END END ] as split_points
WITH study,field, split_points, value, [x in split_points | CASE WHEN x[1] is not null THEN substring(value,x[0],x[1]) ELSE value END] as parts
WITH study,field, CASE WHEN size(parts)>1 THEN apoc.text.join(parts,' \n') ELSE value END as value
with field, apoc.map.fromPairs(collect([study,value])) as map
with field as `Study Field`,map[toString('Base')] as `Base`, map['Compare'] as `Compare`
WITH `Study Field`,`Base`, `Compare`,
CASE WHEN `Base` = `Compare` THEN 'no' ELSE CASE WHEN `Base` is null and `Compare` is null THEN 'no' ELSE 'yes' END END as __Diff
return `Study Field`, `Base`, `Compare`, __Diff

////
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, s.study_id_prefix+'-'+s.study_number as trialid,  CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
with s, trialid, study 
match (s)-[r1]->(txt:StudyField) where txt.field_name is not null
with distinct study, trialid, txt.field_name as field ,CASE WHEN apoc.meta.cypher.type(txt.value) contains 'LIST' THEN apoc.text.join(txt.value,' \n') ELSE toString(txt.value) END as value, 
CASE WHEN not $neodash_wrap_limit ='' THEN $neodash_wrap_limit ELSE 50 END as wrap_limit
WITH study, field, value, apoc.text.indexesOf(value,' ') as space_pos1,
CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit
WITH study,field, space_pos1, CASE wrap_limit WHEN '0' THEN [0] ELSE[x in space_pos1 | x/wrap_limit ] END as div, value
WITH study,field, space_pos1, div, CASE WHEN size(div) >0 THEN apoc.coll.toSet(div) ELSE [-1] END as freq, value
WITH study,field,space_pos1, div, freq, value
UNWIND freq as f
WITH study,field,space_pos1, div, apoc.coll.runningTotal(collect(apoc.coll.occurrences(div,f))) as occ, value
WITH study,field,space_pos1,value, [
    x in RANGE(0,size(occ)-1) | CASE x WHEN 0 THEN [x,occ[x]-1] ELSE [occ[x-1]-1,occ[x]-1] END
    ] as pair, occ
    with study,field, space_pos1, value, occ,[x in pair where x[1] is not null] as pair
WITH study,field, space_pos1, value, pair, occ, 
[x in pair | CASE x[0] WHEN 0 THEN [0,space_pos1[x[1]]] ELSE 
  CASE  WHEN x[0]=pair[size(pair)-1][0] and space_pos1 is not null THEN [space_pos1[x[0]],size(value)] 
  ELSE [space_pos1[x[0]],space_pos1[x[1]]-space_pos1[x[0]]] END END ] as split_points
WITH study,field, split_points, value, [x in split_points | CASE WHEN x[1] is not null THEN substring(value,x[0],x[1]) 
ELSE value END] as parts
WITH study,field, CASE WHEN size(parts)>1 THEN apoc.text.join(parts,'\n') ELSE value END as value
with field, apoc.map.fromPairs(collect([study,value])) as map
with field as `Study Field`,map[toString('Base')] as `Base`, map['Compare'] as `Compare`
WITH `Study Field`,`Base`, `Compare`,
CASE WHEN `Base` = `Compare` THEN 'no' ELSE CASE WHEN `Base` is null and `Compare` is null THEN 'no' ELSE 'yes' END END as __Diff
return `Study Field`, `Base`, `Compare`, __Diff




// current study selection
    //table
    match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
    WITH s,r0, s.study_id_prefix+'-'+s.study_number as trialid, split(apoc.temporal.format(r0.start_date, "iso_local_date_time"),'.')[0] as start_date
    WITH r0, start_date, trialid where trialid in[$neodash_studya, $neodash_studyb] 
    and datetime(start_date) in [datetime($neodash_versiondate_studya),datetime($neodash_versiondate_studyb)]
    with start_date,trialid, r0, CASE when trialid=$neodash_studya then 'Base ('+$neodash_studya+')' ELSE 'Compare ('+$neodash_studyb+')' END as Study
    return Study, 
    trialid as TrialID,
    start_date as StartDate

    //single value
    return 'Base\nTrial ID: '+$neodash_studya+' (StartDate: '+$neodash_versiondate_studya+')\n\n
    Compare\nTrial ID:'+$neodash_studyb+' (StartDate: '+$neodash_versiondate_studyb+')'



//wrap selector
WITH range(0, 95 ,5) as limits UNWIND limits as limit 
WITH limit WHERE toLower(toString(limit)) CONTAINS toLower($input) 
RETURN DISTINCT limit as value,  limit as display ORDER BY size(toString(value)) ASC LIMIT 10


// tab on objective and endpoints
//Endpint(by Objective)
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, s.study_id_prefix+'-'+s.study_number as trialid, 
split(apoc.temporal.format(r0.start_date, "iso_local_date_time"),'.')[0] as start_date
with start_date, s, trialid where trialid in[$neodash_studya, $neodash_studyb] 
and datetime(start_date) in [datetime($neodash_versiondate_studya),datetime($neodash_versiondate_studyb)]
optional match (s)-[r3]->(endp:StudyEndpoint)-[r3_1]->(endp_val:EndpointValue)
optional match (s)-[r4]->(obj:StudyObjective)-[r4_1]->(obj_val:ObjectiveValue)
match(endp)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(obj)
with obj, obj_val, endp, endp_val,
CASE WHEN trialid=$neodash_studya and datetime(start_date)=datetime($neodash_versiondate_studya) THEN 'Base' ELSE 'Compare' END as study, 
'Obj '+toString(obj.order) + ' - Endp '+toString(endp.order) as Number,
obj_val.name_plain as Objective, 
endp_val.name_plain as Endpoint,
CASE WHEN not $neodash_wrap_limit ='' THEN $neodash_wrap_limit ELSE 50 END as wrap_limit order by obj_val.name_plain,endp_val.name_plain
with Number, study, Objective, Endpoint, CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(Objective)='STRING' THEN apoc.text.indexesOf(Objective, ' ')  ELSE null END as obj_space_pos1,
CASE when apoc.meta.cypher.type(Endpoint)='STRING' THEN apoc.text.indexesOf(Endpoint, ' ')  ELSE null END as endp_space_pos1
with Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in obj_space_pos1 | x/wrap_limit ] END as obj_div,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in endp_space_pos1 | x/wrap_limit ] END as endp_div
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,obj_div,endp_div,
CASE WHEN size(obj_div) >0 THEN apoc.coll.toSet(obj_div) ELSE [-1] END as obj_freq
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,obj_div,endp_div, obj_freq
UNWIND obj_freq as obj_f
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,endp_div,
apoc.coll.runningTotal(collect(apoc.coll.occurrences(obj_div,obj_f))) as obj_occ
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1, endp_div, obj_occ,
CASE WHEN size(endp_div) >0 THEN apoc.coll.toSet(endp_div) ELSE [-1] END as endp_freq
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1, obj_occ, endp_div, endp_freq
UNWIND endp_freq as endp_f
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,obj_occ,
apoc.coll.runningTotal(collect(apoc.coll.occurrences(endp_div,endp_f))) as endp_occ
WITH Number, study,Objective, Endpoint, obj_space_pos1, endp_space_pos1, [
    x in RANGE(0,size(obj_occ)-1) | CASE x WHEN 0 THEN [x,obj_occ[x]-1] ELSE [obj_occ[x-1]-1,obj_occ[x]-1] END
    ] as obj_pair, 
    [
    x in RANGE(0,size(endp_occ)-1) | CASE x WHEN 0 THEN [x,endp_occ[x]-1] ELSE [endp_occ[x-1]-1,endp_occ[x]-1] END
    ] as endp_pair
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,
[x in obj_pair where x[1] is not null] as obj_pair,
[x in endp_pair where x[1] is not null] as endp_pair
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,
[x in obj_pair | CASE x[0] WHEN 0 
                 THEN [0,obj_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN obj_pair[size(obj_pair)-1][0] THEN [obj_space_pos1[x[0]],size(Objective)] 
                     ELSE [obj_space_pos1[x[0]],obj_space_pos1[x[1]]-obj_space_pos1[x[0]]] END END ] as obj_split_points,
[x in endp_pair | CASE x[0] WHEN 0 
                 THEN [0,endp_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN endp_pair[size(endp_pair)-1][0] THEN [endp_space_pos1[x[0]],size(Endpoint)] 
                     ELSE [endp_space_pos1[x[0]],endp_space_pos1[x[1]]-endp_space_pos1[x[0]]] END END ] as endp_split_points   
WITH Number, study, Objective, Endpoint,
[x in obj_split_points | CASE WHEN x[1] is not null THEN substring(Objective,x[0],x[1]) ELSE Objective END] as obj_parts,
[x in endp_split_points | CASE WHEN x[1] is not null THEN substring(Endpoint,x[0],x[1]) ELSE Endpoint END] as endp_parts 
WITH Number, study, CASE WHEN size(obj_parts)>1 THEN apoc.text.join(obj_parts,' \n') ELSE Objective END as Objective,
CASE WHEN size(endp_parts)>1 THEN apoc.text.join(endp_parts,' \n') ELSE Endpoint END as Endpoint
with Number, Objective, apoc.map.fromPairs(collect([study,Endpoint])) as map
with Number , Objective,map['Base'] as `Base - Endpoint`, map['Compare'] as `Compare - Endpoint`,
CASE WHEN map['Base'] = map['Compare'] THEN 'no' ELSE CASE WHEN map['Base'] is null and map['Compare'] is null THEN 'no' ELSE 'yes' END END as __Diff order by Number
return Number, Objective, `Base - Endpoint`,`Compare - Endpoint`, __Diff

//new Endpint(by Objective)
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[r3]->(endp:StudyEndpoint)-[r3_1]->(endp_val:EndpointValue)
optional match (s)-[r4]->(obj:StudyObjective)-[r4_1]->(obj_val:ObjectiveValue)
match(endp)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(obj)
with study, obj, obj_val, endp, endp_val,
'Obj '+toString(obj.order) + ' - Endp '+toString(endp.order) as Number,
obj_val.name_plain as Objective, 
endp_val.name_plain as Endpoint,
CASE WHEN not $neodash_wrap_limit ='' THEN $neodash_wrap_limit ELSE 50 END as wrap_limit order by obj_val.name_plain,endp_val.name_plain
with Number, study, Objective, Endpoint, CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(Objective)='STRING' THEN apoc.text.indexesOf(Objective, ' ')  ELSE null END as obj_space_pos1,
CASE when apoc.meta.cypher.type(Endpoint)='STRING' THEN apoc.text.indexesOf(Endpoint, ' ')  ELSE null END as endp_space_pos1
with Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in obj_space_pos1 | x/wrap_limit ] END as obj_div,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in endp_space_pos1 | x/wrap_limit ] END as endp_div
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,obj_div,endp_div,
CASE WHEN size(obj_div) >0 THEN apoc.coll.toSet(obj_div) ELSE [-1] END as obj_freq
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,obj_div,endp_div, obj_freq
UNWIND obj_freq as obj_f
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,endp_div,
apoc.coll.runningTotal(collect(apoc.coll.occurrences(obj_div,obj_f))) as obj_occ
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1, endp_div, obj_occ,
CASE WHEN size(endp_div) >0 THEN apoc.coll.toSet(endp_div) ELSE [-1] END as endp_freq
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1, obj_occ, endp_div, endp_freq
UNWIND endp_freq as endp_f
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,obj_occ,
apoc.coll.runningTotal(collect(apoc.coll.occurrences(endp_div,endp_f))) as endp_occ
WITH Number, study,Objective, Endpoint, obj_space_pos1, endp_space_pos1, [
    x in RANGE(0,size(obj_occ)-1) | CASE x WHEN 0 THEN [x,obj_occ[x]-1] ELSE [obj_occ[x-1]-1,obj_occ[x]-1] END
    ] as obj_pair, 
    [
    x in RANGE(0,size(endp_occ)-1) | CASE x WHEN 0 THEN [x,endp_occ[x]-1] ELSE [endp_occ[x-1]-1,endp_occ[x]-1] END
    ] as endp_pair
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,
[x in obj_pair where x[1] is not null] as obj_pair,
[x in endp_pair where x[1] is not null] as endp_pair
WITH Number, study, Objective, Endpoint, obj_space_pos1, endp_space_pos1,
[x in obj_pair | CASE x[0] WHEN 0 
                 THEN [0,obj_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN obj_pair[size(obj_pair)-1][0] THEN [obj_space_pos1[x[0]],size(Objective)] 
                     ELSE [obj_space_pos1[x[0]],obj_space_pos1[x[1]]-obj_space_pos1[x[0]]] END END ] as obj_split_points,
[x in endp_pair | CASE x[0] WHEN 0 
                 THEN [0,endp_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN endp_pair[size(endp_pair)-1][0] THEN [endp_space_pos1[x[0]],size(Endpoint)] 
                     ELSE [endp_space_pos1[x[0]],endp_space_pos1[x[1]]-endp_space_pos1[x[0]]] END END ] as endp_split_points   
WITH Number, study, Objective, Endpoint,
[x in obj_split_points | CASE WHEN x[1] is not null THEN substring(Objective,x[0],x[1]) ELSE Objective END] as obj_parts,
[x in endp_split_points | CASE WHEN x[1] is not null THEN substring(Endpoint,x[0],x[1]) ELSE Endpoint END] as endp_parts 
WITH Number, study, CASE WHEN size(obj_parts)>1 THEN apoc.text.join(obj_parts,' \n') ELSE Objective END as Objective,
CASE WHEN size(endp_parts)>1 THEN apoc.text.join(endp_parts,' \n') ELSE Endpoint END as Endpoint
with Number, Objective, apoc.map.fromPairs(collect([study,Endpoint])) as map
with Number , Objective,map['Base'] as `Base - Endpoint`, map['Compare'] as `Compare - Endpoint`,
CASE WHEN map['Base'] = map['Compare'] THEN 'no' ELSE CASE WHEN map['Base'] is null and map['Compare'] is null THEN 'no' ELSE 'yes' END END as __Diff order by Number
return Number, Objective, `Base - Endpoint`,`Compare - Endpoint`, __Diff


// Objective by study
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, s.study_id_prefix+'-'+s.study_number as trialid, 
split(apoc.temporal.format(r0.start_date, "iso_local_date_time"),'.')[0] as start_date
with start_date, s, trialid where trialid in[$neodash_studya, $neodash_studyb] 
and datetime(start_date) in [datetime($neodash_versiondate_studya),datetime($neodash_versiondate_studyb)]
optional match (s)-[r3]->(endp:StudyEndpoint)-[r3_1]->(endp_val:EndpointValue)
optional match (s)-[r4]->(obj:StudyObjective)-[r4_1]->(obj_val:ObjectiveValue)
match(endp)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(obj)
with obj, obj_val, endp, endp_val,
CASE WHEN trialid=$neodash_studya and datetime(start_date)=datetime($neodash_versiondate_studya) THEN 'Base' ELSE 'Compare' END as study, 
'Obj '+toString(obj.order) as Number,
obj_val.name_plain as Objective, 
CASE WHEN not $neodash_wrap_limit_2 ='' THEN $neodash_wrap_limit_2 ELSE 50 END as wrap_limit order by obj_val.name_plain,endp_val.name_plain
with Number, study, Objective,CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(Objective)='STRING' THEN apoc.text.indexesOf(Objective, ' ')  ELSE null END as obj_space_pos1
with Number, study, Objective, obj_space_pos1,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in obj_space_pos1 | x/wrap_limit ] END as obj_div
WITH Number, study, Objective,obj_space_pos1, obj_div,
CASE WHEN size(obj_div) >0 THEN apoc.coll.toSet(obj_div) ELSE [-1] END as obj_freq
WITH Number, study, Objective, obj_space_pos1, obj_div,obj_freq
UNWIND obj_freq as obj_f
WITH Number, study, Objective, obj_space_pos1, 
apoc.coll.runningTotal(collect(apoc.coll.occurrences(obj_div,obj_f))) as obj_occ
WITH Number, study,Objective, obj_space_pos1,  [
    x in RANGE(0,size(obj_occ)-1) | CASE x WHEN 0 THEN [x,obj_occ[x]-1] ELSE [obj_occ[x-1]-1,obj_occ[x]-1] END
    ] as obj_pair
WITH Number, study, Objective,  obj_space_pos1, 
[x in obj_pair where x[1] is not null] as obj_pair
WITH Number, study, Objective,  obj_space_pos1, 
[x in obj_pair | CASE x[0] WHEN 0 
                 THEN [0,obj_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN obj_pair[size(obj_pair)-1][0] THEN [obj_space_pos1[x[0]],size(Objective)] 
                     ELSE [obj_space_pos1[x[0]],obj_space_pos1[x[1]]-obj_space_pos1[x[0]]] END END ] as obj_split_points
WITH Number, study, Objective, 
[x in obj_split_points | CASE WHEN x[1] is not null THEN substring(Objective,x[0],x[1]) ELSE Objective END] as obj_parts
WITH Number, study, 
CASE WHEN size(obj_parts)>1 THEN apoc.text.join(obj_parts,' \n') ELSE Objective END as Objective
with Number, apoc.map.fromPairs(collect([study,Objective])) as map
with Number , map['Base'] as `Base - Objective`, map['Compare'] as `Compare - Objective`,
CASE WHEN map['Base'] = map['Compare'] THEN 'no' ELSE CASE WHEN map['Base'] is null and map['Compare'] is null THEN 'no' ELSE 'yes' END END as __Diff order by Number
return Number, `Base - Objective`,`Compare - Objective`, __Diff

// new Objective by study
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[r3]->(endp:StudyEndpoint)-[r3_1]->(endp_val:EndpointValue)
optional match (s)-[r4]->(obj:StudyObjective)-[r4_1]->(obj_val:ObjectiveValue)
match(endp)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(obj)
with study, obj, obj_val, endp, endp_val, 
'Obj '+toString(obj.order) as Number,
obj_val.name_plain as Objective, 
CASE WHEN not $neodash_wrap_limit_2 ='' THEN $neodash_wrap_limit_2 ELSE 50 END as wrap_limit order by obj_val.name_plain,endp_val.name_plain
with Number, study, Objective,CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(Objective)='STRING' THEN apoc.text.indexesOf(Objective, ' ')  ELSE null END as obj_space_pos1
with Number, study, Objective, obj_space_pos1,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in obj_space_pos1 | x/wrap_limit ] END as obj_div
WITH Number, study, Objective,obj_space_pos1, obj_div,
CASE WHEN size(obj_div) >0 THEN apoc.coll.toSet(obj_div) ELSE [-1] END as obj_freq
WITH Number, study, Objective, obj_space_pos1, obj_div,obj_freq
UNWIND obj_freq as obj_f
WITH Number, study, Objective, obj_space_pos1, 
apoc.coll.runningTotal(collect(apoc.coll.occurrences(obj_div,obj_f))) as obj_occ
WITH Number, study,Objective, obj_space_pos1,  [
    x in RANGE(0,size(obj_occ)-1) | CASE x WHEN 0 THEN [x,obj_occ[x]-1] ELSE [obj_occ[x-1]-1,obj_occ[x]-1] END
    ] as obj_pair
WITH Number, study, Objective,  obj_space_pos1, 
[x in obj_pair where x[1] is not null] as obj_pair
WITH Number, study, Objective,  obj_space_pos1, 
[x in obj_pair | CASE x[0] WHEN 0 
                 THEN [0,obj_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN obj_pair[size(obj_pair)-1][0] THEN [obj_space_pos1[x[0]],size(Objective)] 
                     ELSE [obj_space_pos1[x[0]],obj_space_pos1[x[1]]-obj_space_pos1[x[0]]] END END ] as obj_split_points
WITH Number, study, Objective, 
[x in obj_split_points | CASE WHEN x[1] is not null THEN substring(Objective,x[0],x[1]) ELSE Objective END] as obj_parts
WITH Number, study, 
CASE WHEN size(obj_parts)>1 THEN apoc.text.join(obj_parts,' \n') ELSE Objective END as Objective
with Number, apoc.map.fromPairs(collect([study,Objective])) as map
with Number , map['Base'] as `Base - Objective`, map['Compare'] as `Compare - Objective`,
CASE WHEN map['Base'] = map['Compare'] THEN 'no' ELSE CASE WHEN map['Base'] is null and map['Compare'] is null THEN 'no' ELSE 'yes' END END as __Diff order by Number
return Number, `Base - Objective`,`Compare - Objective`, __Diff


//tab with criteria
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, s.study_id_prefix+'-'+s.study_number as trialid, 
split(apoc.temporal.format(r0.start_date, "iso_local_date_time"),'.')[0] as start_date
with start_date, s, trialid where trialid in[$neodash_studya, $neodash_studyb] 
and datetime(start_date) in [datetime($neodash_versiondate_studya),datetime($neodash_versiondate_studyb)]
optional match (s)-[r3]->(endp:StudyCriteria)-[r3_1]->(crit_val:CriteriaValue)
with crit_val,
CASE WHEN trialid=$neodash_studya and datetime(start_date)=datetime($neodash_versiondate_studya) THEN 'Base' ELSE 'Compare' END as study, 
crit_val.name_plain as Criteria, 
CASE WHEN not $neodash_wrap_limit_3 ='' THEN $neodash_wrap_limit_3 ELSE 50 END as wrap_limit order by crit_val.name_plain
with study, Criteria,CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(Criteria)='STRING' THEN apoc.text.indexesOf(Criteria, ' ')  ELSE null END as crit_space_pos1
with study, Criteria, crit_space_pos1,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in crit_space_pos1 | x/wrap_limit ] END as crit_div
WITH study, Criteria,crit_space_pos1, crit_div,
CASE WHEN size(crit_div) >0 THEN apoc.coll.toSet(crit_div) ELSE [-1] END as crit_freq
WITH study, Criteria, crit_space_pos1, crit_div,crit_freq
UNWIND crit_freq as crit_f
WITH study, Criteria, crit_space_pos1, 
apoc.coll.runningTotal(collect(apoc.coll.occurrences(crit_div,crit_f))) as crit_occ
WITH study,Criteria, crit_space_pos1,  [
    x in RANGE(0,size(crit_occ)-1) | CASE x WHEN 0 THEN [x,crit_occ[x]-1] ELSE [crit_occ[x-1]-1,crit_occ[x]-1] END
    ] as crit_pair
WITH study, Criteria,  crit_space_pos1, 
[x in crit_pair where x[1] is not null] as crit_pair
WITH study, Criteria,  crit_space_pos1, 
[x in crit_pair | CASE x[0] WHEN 0 
                 THEN [0,crit_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN crit_pair[size(crit_pair)-1][0] THEN [crit_space_pos1[x[0]],size(Criteria)] 
                     ELSE [crit_space_pos1[x[0]],crit_space_pos1[x[1]]-crit_space_pos1[x[0]]] END END ] as crit_split_points
WITH study, Criteria, 
[x in crit_split_points | CASE WHEN x[1] is not null THEN substring(Criteria,x[0],x[1]) ELSE Criteria END] as crit_parts
WITH study, 
CASE WHEN size(crit_parts)>1 THEN apoc.text.join(crit_parts,' \n') ELSE Criteria END as Criteria
with apoc.map.fromPairs(collect([study,Criteria])) as map
with map['Base'] as `Base - Criteria`, map['Compare'] as `Compare - Criteria`,
CASE WHEN map['Base'] = map['Compare'] THEN 'no' ELSE CASE WHEN map['Base'] is null and map['Compare'] is null THEN 'no' ELSE 'yes' END END as __Diff 
return `Base - Criteria`,`Compare - Criteria`, __Diff

//new - tab with criteria
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[r3]->(endp:StudyCriteria)-[r3_1]->(crit_val:CriteriaValue)
with study, crit_val, 
crit_val.name_plain as Criteria, 
CASE WHEN not $neodash_wrap_limit_3 ='' THEN $neodash_wrap_limit_3 ELSE 50 END as wrap_limit order by crit_val.name_plain
with study, Criteria,CASE WHEN wrap_limit=0 THEN wrap_limit ELSE 100-wrap_limit END as wrap_limit, 
CASE when apoc.meta.cypher.type(Criteria)='STRING' THEN apoc.text.indexesOf(Criteria, ' ')  ELSE null END as crit_space_pos1
with study, Criteria, crit_space_pos1,
CASE wrap_limit WHEN '0' THEN [0] ELSE[x in crit_space_pos1 | x/wrap_limit ] END as crit_div
WITH study, Criteria,crit_space_pos1, crit_div,
CASE WHEN size(crit_div) >0 THEN apoc.coll.toSet(crit_div) ELSE [-1] END as crit_freq
WITH study, Criteria, crit_space_pos1, crit_div,crit_freq
UNWIND crit_freq as crit_f
WITH study, Criteria, crit_space_pos1, 
apoc.coll.runningTotal(collect(apoc.coll.occurrences(crit_div,crit_f))) as crit_occ
WITH study,Criteria, crit_space_pos1,  [
    x in RANGE(0,size(crit_occ)-1) | CASE x WHEN 0 THEN [x,crit_occ[x]-1] ELSE [crit_occ[x-1]-1,crit_occ[x]-1] END
    ] as crit_pair
WITH study, Criteria,  crit_space_pos1, 
[x in crit_pair where x[1] is not null] as crit_pair
WITH study, Criteria,  crit_space_pos1, 
[x in crit_pair | CASE x[0] WHEN 0 
                 THEN [0,crit_space_pos1[x[1]]] 
                 ELSE CASE x[0] 
                     WHEN crit_pair[size(crit_pair)-1][0] THEN [crit_space_pos1[x[0]],size(Criteria)] 
                     ELSE [crit_space_pos1[x[0]],crit_space_pos1[x[1]]-crit_space_pos1[x[0]]] END END ] as crit_split_points
WITH study, Criteria, 
[x in crit_split_points | CASE WHEN x[1] is not null THEN substring(Criteria,x[0],x[1]) ELSE Criteria END] as crit_parts
WITH study, 
CASE WHEN size(crit_parts)>1 THEN apoc.text.join(crit_parts,' \n') ELSE Criteria END as Criteria
with apoc.map.fromPairs(collect([study,Criteria])) as map
with map['Base'] as `Base - Criteria`, map['Compare'] as `Compare - Criteria`,
CASE WHEN map['Base'] = map['Compare'] THEN 'no' ELSE CASE WHEN map['Base'] is null and map['Compare'] is null THEN 'no' ELSE 'yes' END END as __Diff 
return `Base - Criteria`,`Compare - Criteria`, __Diff

//tab with study visits - the $neodash_sstdtc is a parameter select as datepicker.
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[:HAS_STUDY_VISIT]->(vis)
optional match(vis)-[:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
optional match(vis)-[:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
with s, study, vis, dur_days, vis_name order by id(s), vis.visit_number
with distinct s, study, vis, CASE WHEN study='Base' THEN {duration:dur_days.value,visit_name:'Base: '+vis_name.name+'; Day: '+toString(toInteger(dur_days.value)),study_id:study, visit_number:vis.visit_number} ELSE  {duration:dur_days.value,visit_name:'Compare: '+vis_name.name+'; Day: '+toString(toInteger(dur_days.value)),study_id:study, visit_number:vis.visit_number} END as prop
with s, study, vis, apoc.create.vNode(["Visit"],
properties({visit_number:prop['visit_number'],
            duration:toInteger(prop['duration']),
            visit_name:prop['visit_name'],
            startDate:date($neodash_sstdtc)+Duration({days:(prop['duration'])}), 
            endDate:date($neodash_sstdtc)+Duration({days:(prop['duration'])}),
            study_id:prop['study_id']
            })) as v_visit
with s, study, collect(vis) as visits, collect(v_visit) as v_visits
with s, study, visits, v_visits, [n in RANGE(0,size(v_visits)-2) | apoc.create.vRelationship(v_visits[n],"FOLLOWS",{type:"logical",study:id(s)},v_visits[n+1]) ]as v_rels, range(0,size(v_visits)-1,1) AS coll_size 
with s,study, visits, v_visits,v_rels, coll_size 
UNWIND coll_size AS idx
WITH s, study, visits[idx] as visit,v_visits[idx] as v_visit, v_rels[idx] as v_rel
return distinct study, visit.visit_number as visit, v_visit, v_rel

//Timeline visits  - with colour in properties
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[:HAS_STUDY_VISIT]->(vis)
optional match(vis)-[:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
optional match(vis)-[:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
with s, study, vis, dur_days, vis_name order by id(s), vis.visit_number
with distinct s, study, dur_days.value as duration,vis, 
CASE WHEN study='Base' THEN {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:vis.visit_number,study_id:study} ELSE  {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:vis.visit_number,study_id:study} END as prop order by duration, study
with duration, collect(distinct prop) as props
with duration, [x in range(0,size(props)-1,1) |
CASE WHEN size(props)=2 and not props[0].visit_number = props[1].visit_number 
THEN apoc.create.vNode(["Visit"],
{visit_number:("<p style='color:green;'>Base: " + props[0].visit_number + "</p><p style='color:red;'>Comp: " + props[1].visit_number + "</p>"),
            duration:toInteger(duration),
            visit_name:("<p style='color:green;'>Base: " + props[0].visit_name + "</p><p style='color:red;'>Comp: " + props[1].visit_name + "</p>"),
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            }) 
            ELSE 
            CASE WHEN size(props)=2 and props[0].visit_number = props[1].visit_number
            THEN apoc.create.vNode(["Visit"],
            {visit_number: props[0].visit_number,
            duration:toInteger(duration),
            visit_name:substring(props[x].study_id,0,4)+': '+props[0].visit_name,
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            }) ELSE 
            CASE WHEN size(props)<2 and props[x].study_id='Base' 
                THEN apoc.create.vNode(["Visit"],
            {visit_number:("<p style='color:green;'>Base: " + props[x].visit_number + "</p><p style='color:red;'>Comp: Null </p>"),
            duration:toInteger(duration),
            visit_name:("<p style='color:green;'>Base:" + props[x].visit_name + "</p><p style='color:red;Comp:'> Null </p>"),
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            })  ELSE
            CASE WHEN size(props)<2 and props[x].study_id='Compare' 
                THEN apoc.create.vNode(["Visit"],
{visit_number:("<p style='color:green;'>Base: Null </p><p style='color:red;'>Comp: " + props[x].visit_number + "</p>"),
            duration:toInteger(duration),
            visit_name:("<p style='color:green;Base:'> Null</p><p style='color:red;Comp:'>" + props[x].visit_name),
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            })END END END END] as v_visits
with duration, v_visits
UNWIND v_visits as v_visit
with duration, apoc.any.property(v_visit,'study_id') as study, v_visit
with study, collect(duration) as durations, collect(v_visit) as v_visits
with study, durations, v_visits, [n in RANGE(0,size(v_visits)-2) | apoc.create.vRelationship(v_visits[n],"FOLLOWS",{type:"logical"},v_visits[n+1]) ]as v_rels, range(0,size(v_visits)-1,1) AS coll_size 
with study, durations, v_visits,v_rels, coll_size 
UNWIND coll_size AS idx
WITH  study, durations[idx] as duration,
v_visits[idx] as v_visit, v_rels[idx] as v_rel
return v_visit,v_rel

///

//Table with visit duration differences
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[:HAS_STUDY_VISIT]->(vis)
optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
optional match(vis)-[r]->(x_r)-[:HAS_VERSION]->(x) where not type(r)='HAS_VISIT_NAME' 
with study, x, [k in keys(vis) where not k='uid']  as vis_keys, properties(vis) as vis_props, vis_name.name as `Visit Name`, vis.visit_number as `Visit Number`, [i in labels(x) where not (i contains 'ConceptValue' or i contains 'Template' or i contains 'Numeric' or i contains 'VisitName') ][0] as types
with study, `Visit Name`, `Visit Number`, substring(types,0, size(types)-5) as type, x, vis_keys, vis_props, range(0,size(vis_keys)-1,1) AS coll_size 
with study, `Visit Name`, `Visit Number`, type, CASE when x.value is null then x.name ELSE x.value+' ('+x.name+')' END as value, vis_keys, vis_props, coll_size 
with study, `Visit Name`, `Visit Number`, collect(apoc.map.fromPairs([[type,value]])) as map, [k in vis_keys | apoc.map.fromPairs([[apoc.text.capitalize(replace(k,'_',' ')),apoc.text.capitalize(toLower(replace(toString(vis_props[k]),'_',' ')))]])] as add_maps
with study, `Visit Name`, `Visit Number`, apoc.map.mergeList(apoc.coll.flatten([map,add_maps])) as map
with study, `Visit Name`, `Visit Number`, map,  range(0,size(keys(map))-1,1) AS coll_size 
UNWIND coll_size AS idx
with study, `Visit Name`, `Visit Number`, keys(map)[idx] as type, map[keys(map)[idx]] as value
with `Visit Name`, `Visit Number`, type,  apoc.map.fromPairs(collect([study,value]))  as visit_info_map
return
`Visit Name`, 
`Visit Number`, 
type as `Visit Property Type`, 
visit_info_map['Base'] as `Base`, 
visit_info_map['Compare'] as `Compare`,
CASE WHEN visit_info_map['Base'] = visit_info_map['Compare'] THEN 'no' ELSE 'yes' END as Changed order by  `Visit Number`,`Visit Property Type`

//Study collections
match(s:StudyValue)  where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, id(s) as sid, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match(s)-[:HAS_STUDY_VISIT]->(vis:StudyVisit)
optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
optional match(vis)-[:STUDY_VISIT_HAS_SCHEDULE]->(schedule:StudyActivitySchedule)
optional match (s)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(schedule),
(schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(act:StudyActivity),
(act)-[:HAS_SELECTED_ACTIVITY]->(act_val:ActivityValue),(act)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(ai_s:StudyActivityInstance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]-(ai:ActivityInstanceValue),
(ai)-[r1]->(g)<-[r2]-(act_val)
with distinct vis.visit_number as `Visit ID`,vis.short_visit_label as `Visit Short Label`, act_val.name as Activity, apoc.map.fromPairs(collect([study,'x'])) as map
where Activity is not null
with `Visit ID`,`Visit Short Label`,Activity, map['Base'] as `Base - collection`, map['Compare'] as `Compare - collection` order by `Visit ID`, Activity
with `Visit ID`,`Visit Short Label`,Activity,`Base - collection`,`Compare - collection`, CASE WHEN `Base - collection`='x' and  `Compare - collection` is null then 'Added' ELSE CASE WHEN `Base - collection` is null and  `Compare - collection`='x' THEN 'Deleted' END END as `Change Type`
return `Visit ID`,`Visit Short Label`,Activity,`Base - collection`,`Compare - collection`, `Change Type`

//Activities detail comparison
match(s:StudyValue)  where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, id(s) as sid, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(schedule),
(schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(act:StudyActivity),
(act)-[:HAS_SELECTED_ACTIVITY]->(act_val:ActivityValue),(act)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(ai_s:StudyActivityInstance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]-(ai:ActivityInstanceValue),
(ai)-[r1]->(g)<-[r2]-(act_val)
optional match(act)-[r3:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(x)-[:HAS_FLOWCHART_GROUP]->(ct_root:CTTermRoot)-[:HAS_NAME_ROOT]->(ct_name_root:CTTermNameRoot)-[:LATEST]->(flowchart_grp:CTTermNameValue)
optional match(act)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(s_act_grp)-[:HAS_SELECTED_ACTIVITY_GROUP]->(group:ActivityGroupValue)
optional match(act)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(s_act_s_grp)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(s_group:ActivitySubGroupValue)
with study, flowchart_grp.name as flowchart_grp, group.name as group, s_group.name as s_group, act_val.name+'(Data collection: '+act_val.is_data_collected+')' as act_detail
with act_detail, apoc.map.fromPairs(collect([study,flowchart_grp])) as flowchart_grp,apoc.map.fromPairs(collect([study,group])) as group,
apoc.map.fromPairs(collect([study,s_group])) as s_group
with flowchart_grp['Base'] as `Flowchart Group (Base)`, group['Base'] as `Activity Group (Base)`,s_group['Base'] as `Activity Subgroup (Base)`, flowchart_grp['Compare'] as `Flowchart Group (Compare)`, group['Compare'] as `Activity Group (Compare)`,s_group['Compare'] as `Activity Subgroup (Compare)`,
 act_detail as `Activity Detail` where `Activity Detail` is not null
 with `Flowchart Group (Base)`,`Activity Group (Base)`,`Activity Subgroup (Base)`,
 `Flowchart Group (Compare)`,`Activity Group (Compare)`,`Activity Subgroup (Compare)`,`Activity Detail`, 
 CASE WHEN `Flowchart Group (Base)` is not null and `Flowchart Group (Compare)` is null THEN 'Activity Added' 
     ELSE 
     CASE WHEN `Flowchart Group (Base)` is null and `Flowchart Group (Compare)` is not null THEN 'Activity deleted' ELSE 
        CASE WHEN (not `Flowchart Group (Base)`= `Flowchart Group (Compare)`) OR (not `Activity Group (Base)`=`Activity Group (Compare)`) OR (not `Activity Subgroup (Base)`=`Activity Subgroup (Compare)`) THEN 'Activity moved' END END END as `Change Type`
 return `Change Type`,`Flowchart Group (Base)`,`Activity Group (Base)`,`Activity Subgroup (Base)`,
 `Flowchart Group (Compare)`,`Activity Group (Compare)`,`Activity Subgroup (Compare)`,`Activity Detail`

//export to Liam
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue) 
match (p:Project)-[r8:HAS_FIELD]->(sp:StudyProjectField)<-[r9:HAS_PROJECT]-(s)
optional match (s)-[r1:HAS_STUDY_VISIT]->(vis)
optional match(s)<-[r10:AFTER]-(sact:StudyAction)
optional match(vis)-[r2:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[r3:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
optional match(vis)-[r4:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[r5:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
optional match(vis)-[r6:HAS_VISIT_NAME]->(vis_name_root)-[r7:HAS_VERSION]->(vis_name:VisitNameValue)
with collect(DISTINCT sact)+collect(DISTINCT sr)+collect(DISTINCT p)+ collect(DISTINCT sp)+collect(DISTINCT s) + collect(DISTINCT  vis) + collect(DISTINCT  dur_day_root) + collect(DISTINCT  dur_days) + collect(DISTINCT  dur_wk_root) + collect(DISTINCT  dur_week) + collect(DISTINCT  vis_name_root) + collect(DISTINCT  vis_name)  AS importNodes, collect(r0)+collect(r1)+collect(r2)+collect(r3)+collect(r4)+collect(r5)+collect(r6)+collect(r7)+collect(r8)+collect(r9)+collect(r10) AS importRels
CALL apoc.export.cypher.data(importNodes, importRels,
  "export-cypher-format-addStructure.cypher",
  { format: "plain", cypherFormat: "addStructure" })
YIELD file, batches, source, format, nodes, relationships, properties, time, rows, batchSize
RETURN file, batches, source, format, nodes, relationships, properties, time, rows, batchSize;

//export for activity testing
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue) 
match (p:Project)-[r1:HAS_FIELD]->(sp:StudyProjectField)<-[r2:HAS_PROJECT]-(s)
optional match (s)-[r3:HAS_STUDY_ACTIVITY_SCHEDULE]->(schedule),
(schedule)<-[r4:STUDY_ACTIVITY_HAS_SCHEDULE]-(act:StudyActivity),
(act)-[r5:HAS_SELECTED_ACTIVITY]->(act_val:ActivityValue),(act)-[r6:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(ai_s:StudyActivityInstance)-[r7:HAS_SELECTED_ACTIVITY_INSTANCE]-(ai:ActivityInstanceValue),
(ai)-[r16]->(g)<-[r17]-(act_val)
optional match(act)-[r8:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(x)-[r9:HAS_FLOWCHART_GROUP]->(ct_root:CTTermRoot)-[r10:HAS_NAME_ROOT]->(ct_name_root:CTTermNameRoot)-[r11:LATEST]->(flowchart_grp:CTTermNameValue)
optional match(act)-[r12:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(s_act_grp)-[r13:HAS_SELECTED_ACTIVITY_GROUP]->(group:ActivityGroupValue)
optional match(act)-[r14:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(s_act_s_grp)-[r15:HAS_SELECTED_ACTIVITY_SUBGROUP]->(s_group:ActivitySubGroupValue)
with collect(DISTINCT sr)+collect(DISTINCT p)+ collect(DISTINCT sp)+collect(DISTINCT s) + collect(DISTINCT schedule)+ collect(DISTINCT act)+ collect(DISTINCT act_val)+collect(DISTINCT ai_s)+collect(DISTINCT ai)+ collect(DISTINCT g)+collect(DISTINCT act_val)+collect(DISTINCT x)+collect(DISTINCT ct_root)+collect(DISTINCT ct_name_root)+collect(DISTINCT flowchart_grp)+collect(DISTINCT s_act_grp)+collect(DISTINCT s_act_s_grp)+collect(DISTINCT group)+collect(DISTINCT s_group) AS importNodes, collect(r0)+collect(r1)+collect(r2)+collect(r3)+collect(r4)+collect(r5)+collect(r6)+collect(r7)+collect(r8)+collect(r9)+collect(r10)+collect(r11) +collect(r12)+collect(r13)+collect(r14)+collect(r15)+collect(r16)+collect(r17)AS importRels
CALL apoc.export.cypher.data(importNodes, importRels,
  "activity_export.cypher",
  { format: "plain", cypherFormat: "addStructure" })
YIELD file, batches, source, format, nodes, relationships, properties, time, rows, batchSize
RETURN file, batches, source, format, nodes, relationships, properties, time, rows, batchSize;



///codelist
MATCH (n1:CTCodelistAttributesValue)<--(:CTCodelistAttributesRoot)<--(n3:CTCodelistRoot)
    -->(tr:CTTermRoot)-->(tar:CTTermAttributesRoot)-[v:HAS_VERSION]->(tav:CTTermAttributesValue)
WHERE n1.name=$neodash_ctcodelistattributesvalue_name
WITH DISTINCT tr, tar, v, tav ORDER BY v.start_date
CALL {
    WITH tar, v
    WITH tar, v.start_date AS date
    MATCH (tar)-[v2:HAS_VERSION]->(tav2)
    WHERE v2.start_date > date
    RETURN v2, tav2 ORDER BY v2.start_date LIMIT 1
}
CALL apoc.create.vNode(["Term"],
  {start_date:date(v.start_date),
  end_date:coalesce(date(v.end_date), date("2025-01-01")),
  concept_id:("<p style='color:green;'>V1: " + coalesce(tav.concept_id, "Sponsor") + "</p><p style='color:red;'>V2: " + coalesce(tav2.concept_id, "Sponsor") + "</p>"),
  code_submission_value:tav.code_submission_value,
  diff_code_submission_value:("<p style='color:green;'>V1: " + tav.code_submission_value + "</p><p style='color:red;'>V2: " + tav2.code_submission_value + "</p>"),
  name_submission_value: ("<p style='color:green;'>V1: " + coalesce(tav.name_submission_value, "None") + "</p><p style='color:red;'>V2: " + coalesce(tav2.name_submission_value, "None") + "</p>"),
  definition:("<p style='color:green;'>V1: " + tav.definition + "</p><p style='color:red;'>V2: " + tav2.definition + "</p>"),
  preferred_term:("<p style='color:green;'>V1: " + tav.preferred_term + "</p><p style='color:red;'>V2: " + tav2.preferred_term + "</p>"),
  synonyms:("<p style='color:green;'>V1: " + coalesce(tav.synonyms, "None") + "</p><p style='color:red;'>V2: " + coalesce(tav2.synonyms, "None") + "</p>")
  })
YIELD node as prevTerm
CALL apoc.create.vNode(["Term"],
  {start_date:date(v2.start_date),
  end_date:coalesce(date(v2.end_date), date("2025-01-01")),
  concept_id:("<p style='color:green;'>V1: " + coalesce(tav.concept_id, "Sponsor") + "</p><p style='color:red;'>V2: " + coalesce(tav2.concept_id, "Sponsor") + "</p>"),
  code_submission_value:tav2.code_submission_value,
  diff_code_submission_value:("<p style='color:green;'>V1: " + tav.code_submission_value + "</p><p style='color:red;'>V2: " + tav2.code_submission_value + "</p>"),
  name_submission_value: ("<p style='color:green;'>V1: " + coalesce(tav.name_submission_value, "None") + "</p><p style='color:red;'>V2: " + coalesce(tav2.name_submission_value, "None") + "</p>"),
  definition:("<p style='color:green;'>V1: " + tav.definition + "</p><p style='color:red;'>V2: " + tav2.definition + "</p>"),
  preferred_term:("<p style='color:green;'>V1: " + tav.preferred_term + "</p><p style='color:red;'>V2: " + tav2.preferred_term + "</p>"),
  synonyms:("<p style='color:green;'>V1: " + coalesce(tav.synonyms, "None") + "</p><p style='color:red;'>V2: " + coalesce(tav2.synonyms, "None") + "</p>")
  })
YIELD node as nextTerm
CALL apoc.create.vRelationship(prevTerm, 'NEXT', {}, nextTerm) yield rel as rel
RETURN tr.uid AS term_uid, tav.code_submission_value AS code_submission_value, prevTerm, rel, nextTerm ORDER BY term_uid

UNION
MATCH (n1:CTCodelistAttributesValue)<--(:CTCodelistAttributesRoot)<--(n3:CTCodelistRoot)
    -->(tr:CTTermRoot)-->(tar:CTTermAttributesRoot)-[v:HAS_VERSION]->(tav:CTTermAttributesValue)
WHERE n1.name=$neodash_ctcodelistattributesvalue_name
WITH DISTINCT tr, tar, collect(DISTINCT v) AS all_v
WHERE size(all_v)=1
UNWIND all_v AS v
MATCH (tar)-[v]->(tav)
CALL apoc.create.vNode(["Term"],
  {start_date:date(v.start_date),
  end_date:coalesce(date(v.end_date), date("2025-01-01")),
  concept_id:coalesce(tav.concept_id, "Sponsor"),
  code_submission_value:tav.code_submission_value,
  name_submission_value: coalesce(tav.name_submission_value, "None"),
  definition:tav.definition,
  preferred_term:tav.preferred_term,
  synonyms:coalesce(tav.synonyms, "None")
})
YIELD node as prevTerm
RETURN DISTINCT tr.uid AS term_uid, tav.code_submission_value AS code_submission_value, prevTerm, NULL AS rel, NULL AS nextTerm ORDER BY term_uid


///color coding

with 'Visit 3; Day: 84' as s1, 'Visit 4; Day: 84 bl bls' as s2
with s1, s2, range(0,apoc.coll.max([size(s1),size(s2)]-1)) as r
WITH s1, s2, [x in r | CASE WHEN substring(s1,x,1)=substring(s2,x,1) and substring(s1,x,1) is not null
THEN '<p style="background-color:#e6ffec;color:#1F2328">'+substring(s1,x,1)+'</p>' 
ELSE CASE WHEN substring(s1,x,1) is not null 
THEN '<p style="background-color:#abf2bc;color:#1F2328">'+substring(s1,x,1)+'</p>' END END ] as s1_colour,
[x in r | 
CASE WHEN substring(s1,x,1)=substring(s2,x,1) and substring(s2,x,1) is not null 
THEN '<p style="background-color:#ffebe9;color:#1F2328">'+substring(s2,x,1)+'</p>' 
    ELSE CASE WHEN substring(s2,x,1) is not null
THEN '<p style="background-color:#ff818266;color:#1F2328">'+substring(s2,x,1)+'</p>' END END ] as s2_colour
with apoc.text.join(s1_colour,'') as s1_c, apoc.text.join(s2_colour,'') as s2_c
return +s1_c+'\n'+s2_c as diff

("<p style='color:green;'>Base: " + props[0].visit_number + "</p><p style='color:red;'>Comp: " + props[1].visit_number + "</p>")

[x in range(0,apoc.coll.max([size(props[0].visit_number),size(props[1].visit_number)])-1) | CASE WHEN substring(props[0].visit_number,x,1)=substring(props[1].visit_number,x,1) and substring(props[0].visit_number,x,1) is not null
THEN '<p style="background-color:#e6ffec;color:#1F2328">'+substring(props[0].visit_number,x,1)+'</p>' 
ELSE CASE WHEN substring(props[0].visit_number,x,1) is not null 
THEN '<p style="background-color:#abf2bc;color:#1F2328">'+substring(props[0].visit_number,x,1)+'</p>' END END ] as p1,
[x in range(0,apoc.coll.max([size(props[0].visit_number),size(props[1].visit_number)])-1) | 
CASE WHEN substring(props[0].visit_number,x,1)=substring(props[1].visit_number,x,1) and substring(props[1].visit_number,x,1) is not null 
THEN '<p style="background-color:#ffebe9;color:#1F2328">'+substring(props[1].visit_number,x,1)+'</p>' 
    ELSE CASE WHEN substring(props[1].visit_number,x,1) is not null
THEN '<p style="background-color:#ff818266;color:#1F2328">'+substring(props[1].visit_number,x,1)+'</p>' END END ] as p2,

[x in range(0,apoc.coll.max([size(props[0].visit_name),size(props[1].visit_name)])-1) | CASE WHEN substring(props[0].visit_name,x,1)=substring(props[1].visit_name,x,1) and substring(props[0].visit_name,x,1) is not null
THEN '<p style="background-color:#e6ffec;color:#1F2328">'+substring(props[0].visit_name,x,1)+'</p>' 
ELSE CASE WHEN substring(props[0].visit_name,x,1) is not null 
THEN '<p style="background-color:#abf2bc;color:#1F2328">'+substring(props[0].visit_name,x,1)+'</p>' END END ] as p3,
[x in range(0,apoc.coll.max([size(props[0].visit_name),size(props[1].visit_name)])-1) | 
CASE WHEN substring(props[0].visit_name,x,1)=substring(props[1].visit_name,x,1) and substring(props[1].visit_name,x,1) is not null 
THEN '<p style="background-color:#ffebe9;color:#1F2328">'+substring(props[1].visit_name,x,1)+'</p>' 
    ELSE CASE WHEN substring(props[1].visit_name,x,1) is not null
THEN '<p style="background-color:#ff818266;color:#1F2328">'+substring(props[1].visit_number,x,1)+'</p>' END END ] as p4,
with apoc.text.join(p1,'')+'\n'+apoc.text.join(p2,'') as vis_num_diff, apoc.text.join(p3,'')+'\n'+apoc.text.join(p4,'') as vis_name_diff

///Timeline  - new color
match(s:StudyValue) where id(s) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[:HAS_STUDY_VISIT]->(vis)
optional match(vis)-[:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
optional match(vis)-[:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
with s, study, vis, dur_days, vis_name order by id(s), vis.visit_number
with distinct s, study, dur_days.value as duration,vis, 
CASE WHEN study='Base' THEN {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:toString(vis.visit_number),study_id:study} ELSE  {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:toString(vis.visit_number),study_id:study} END as prop order by duration, study
with duration, collect(distinct prop) as props
with props, duration,
[x in range(0,apoc.coll.max([size(props[0].visit_number),size(props[1].visit_number)])-1) | CASE WHEN substring(props[0].visit_number,x,1)=substring(props[1].visit_number,x,1) and substring(props[0].visit_number,x,1) is not null
THEN '<p style="background-color:#e6ffec;color:#1F2328">'+substring(props[0].visit_number,x,1)+'</p>' 
ELSE CASE WHEN substring(props[0].visit_number,x,1) is not null 
THEN '<p style="background-color:#abf2bc;color:#1F2328">'+substring(props[0].visit_number,x,1)+'</p>' END END ] as p1,
[x in range(0,apoc.coll.max([size(props[0].visit_number),size(props[1].visit_number)])-1) | 
CASE WHEN substring(props[0].visit_number,x,1)=substring(props[1].visit_number,x,1) and substring(props[1].visit_number,x,1) is not null 
THEN '<p style="background-color:#ffebe9;color:#1F2328">'+substring(props[1].visit_number,x,1)+'</p>' 
    ELSE CASE WHEN substring(props[1].visit_number,x,1) is not null
THEN '<p style="background-color:#ff818266;color:#1F2328">'+substring(props[1].visit_number,x,1)+'</p>' END END] as p2,
[x in range(0,apoc.coll.max([size(props[0].visit_name),size(props[1].visit_name)])-1) | CASE WHEN substring(props[0].visit_name,x,1)=substring(props[1].visit_name,x,1) and substring(props[0].visit_name,x,1) is not null
THEN '<p style="background-color:#e6ffec;color:#1F2328">'+substring(props[0].visit_name,x,1)+'</p>' 
ELSE CASE WHEN substring(props[0].visit_name,x,1) is not null 
THEN '<p style="background-color:#abf2bc;color:#1F2328">'+substring(props[0].visit_name,x,1)+'</p>' END END ] as p3,
[x in range(0,apoc.coll.max([size(props[0].visit_name),size(props[1].visit_name)])-1) | 
CASE WHEN substring(props[0].visit_name,x,1)=substring(props[1].visit_name,x,1) and substring(props[1].visit_name,x,1) is not null 
THEN '<p style="background-color:#ffebe9;color:#1F2328">'+substring(props[1].visit_name,x,1)+'</p>' 
    ELSE CASE WHEN substring(props[1].visit_name,x,1) is not null
THEN '<p style="background-color:#ff818266;color:#1F2328">'+substring(props[1].visit_number,x,1)+'</p>' END END ] as p4
with duration, props, apoc.text.join(p1,'')+'\n'+apoc.text.join(p2,'') as vis_num_diff, apoc.text.join(p3,'')+'\n'+apoc.text.join(p4,'') as vis_name_diff
with duration, vis_num_diff, vis_name_diff, [x in range(0,size(props)-1,1) |
CASE WHEN size(props)=2 and not props[0].visit_number = props[1].visit_number 
THEN apoc.create.vNode(["Visit"],
{visit_number:('Base:'+vis_num_diff +'Comp:'+vis_num_diff),
            duration:toInteger(duration),
            visit_name:('Base:' +vis_name_diff+'Comp:'+vis_name_diff),
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            }) 
            ELSE 
            CASE WHEN size(props)=2 and props[0].visit_number = props[1].visit_number
            THEN apoc.create.vNode(["Visit"],
            {visit_number: props[0].visit_number,
            duration:toInteger(duration),
            visit_name:substring(props[x].study_id,0,4)+': '+props[0].visit_name,
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            }) ELSE 
            CASE WHEN size(props)<2 and props[x].study_id='Base' 
                THEN apoc.create.vNode(["Visit"],
            {visit_number:("<p style='color:green;'>Base: " + props[x].visit_number + "</p><p style='color:red;'>Comp: Null </p>"),
            duration:toInteger(duration),
            visit_name:("<p style='color:green;'>Base:" + props[x].visit_name + "</p><p style='color:red;Comp:'> Null </p>"),
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            })  ELSE
            CASE WHEN size(props)<2 and props[x].study_id='Compare' 
                THEN apoc.create.vNode(["Visit"],
{visit_number:("<p style='color:green;'>Base: Null </p><p style='color:red;'>Comp: " + props[x].visit_number + "</p>"),
            duration:toInteger(duration),
            visit_name:("<p style='color:green;Base:'> Null</p><p style='color:red;Comp:'>" + props[x].visit_name),
            startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
            endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
            study_id:props[x].study_id,
            visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
            })END END END END] as v_visits
with duration, v_visits
UNWIND v_visits as v_visit
with duration, apoc.any.property(v_visit,'study_id') as study, v_visit
with study, collect(duration) as durations, collect(v_visit) as v_visits
with study, durations, v_visits, [n in RANGE(0,size(v_visits)-2) | apoc.create.vRelationship(v_visits[n],"FOLLOWS",{type:"logical"},v_visits[n+1]) ]as v_rels, range(0,size(v_visits)-1,1) AS coll_size 
with study, durations, v_visits,v_rels, coll_size 
UNWIND coll_size AS idx
WITH  study, durations[idx] as duration,v_visits[idx] as v_visit, v_rels[idx] as v_rel
return v_visit,v_rel


//Visit timeline - account for empty studies
match(st:StudyValue) where id(st) in[toInteger($neodash_studya),toInteger($neodash_studyb)]
with collect(st) as st
call apoc.when(size(st)>0,
"with $t as t
UNWIND t as s 
with s, CASE when id(s)=toInteger($studya) then 'Base' ELSE 'Compare' END as study
optional match (s)-[:HAS_STUDY_VISIT]->(vis)
WITH distinct s, apoc.coll.toSet(collect(vis.short_visit_label)) as vis, study
call apoc.when(size(vis)=0,\"return $study as Study, 'FALSE' as HasVisit\",\"return $study as Study, 'TRUE' as HasVisit\",{study:study,vis:vis}) yield value 
with apoc.map.fromPairs(collect([value.Study,value.HasVisit])) as visitmap
with visitmap
call apoc.case([
 visitmap['Base']='TRUE' and visitmap['Compare']='TRUE', 
            \"with $t as t
            UNWIND t as s 
            with s, CASE when id(s)=toInteger($neodash_studya) then 'Base' ELSE 'Compare' END as study
            optional match (s)-[:HAS_STUDY_VISIT]->(vis)
            optional match(vis)-[:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
            optional match(vis)-[:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
            optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
            with s, study, vis, dur_days, vis_name order by id(s), vis.visit_number
            with distinct s, study, dur_days.value as duration,vis, 
            CASE WHEN study='Base' THEN {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:vis.visit_number,study_id:study} ELSE  {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:vis.visit_number,study_id:study} END as prop order by duration, study
            with duration, collect(distinct prop) as props
            with duration, [x in range(0,size(props)-1,1) |
            CASE WHEN size(props)=2 and not props[0].visit_number = props[1].visit_number 
            THEN apoc.create.vNode([\\\"Visit\\\"],
            {visit_number:(\\\"<p style='color:green;'>Base: \\\" + props[0].visit_number + \\\"</p><p style='color:red;'>Comp: \\\" + props[1].visit_number + \\\"</p>\\\"),
                        duration:toInteger(duration),
                        visit_name:(\\\"<p style='color:green;'>Base: \\\" + props[0].visit_name + \\\"</p><p style='color:red;'>Comp: \\\" + props[1].visit_name + \\\"</p>\\\"),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        }) 
                        ELSE 
                        CASE WHEN size(props)=2 and props[0].visit_number = props[1].visit_number
                        THEN apoc.create.vNode([ \\\"Visit \\\"],
                        {visit_number: props[0].visit_number,
                        duration:toInteger(duration),
                        visit_name:substring(props[x].study_id,0,4)+': '+props[0].visit_name,
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        }) ELSE 
                        CASE WHEN size(props)<2 and props[x].study_id='Base' 
                            THEN apoc.create.vNode([ \\\"Visit \\\"],
                        {visit_number:( \\\"<p style='color:green;'>Base:  \\\" + props[x].visit_number +  \\\"</p><p style='color:red;'>Comp: Null </p> \\\"),
                        duration:toInteger(duration),
                        visit_name:( \\\"<p style='color:green;'>Base:  \\\" + props[x].visit_name +  \\\"</p><p style='color:red;'>Comp: Null </p> \\\"),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        })  ELSE
                        CASE WHEN size(props)<2 and props[x].study_id='Compare' 
                            THEN apoc.create.vNode([ \\\"Visit \\\"],
            {visit_number:( \\\"<p style='color:green;'>Base: Null </p><p style='color:red;'>Comp:  \\\" + props[x].visit_number +  \\\"</p> \\\"),
                        duration:toInteger(duration),
                        visit_name:( \\\"<p style='color:green;'>Base: Null</p><p style='color:red;'>Comp:  \\\" + props[x].visit_name),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        })END END END END] as v_visits
            with duration, v_visits
            UNWIND v_visits as v_visit
            with duration, apoc.any.property(v_visit,'study_id') as study, v_visit
            with study, collect(duration) as durations, collect(v_visit) as v_visits
            with study, durations, v_visits, [n in RANGE(0,size(v_visits)-2) | apoc.create.vRelationship(v_visits[n], \\\"FOLLOWS \\\",{type: \\\"logical \\\"},v_visits[n+1]) ]as v_rels, range(0,size(v_visits)-1,1) AS coll_size 
            with study, durations, v_visits,v_rels, coll_size 
            UNWIND coll_size AS idx
            WITH  study, durations[idx] as duration,
            v_visits[idx] as v_visit, v_rels[idx] as v_rel
            return v_visit,v_rel\",
 visitmap['Base']='TRUE' and visitmap['Compare']='FALSE', 
            \"with $t as t
            UNWIND t as s 
            with s, CASE when id(s)=toInteger($neodash_studya) THEN 'Base' END as study
            optional match (s)-[:HAS_STUDY_VISIT]->(vis)
            optional match(vis)-[:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
            optional match(vis)-[:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
            optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
            with s, study, vis, dur_days, vis_name order by id(s), vis.visit_number
            with distinct s, study, dur_days.value as duration,vis, 
            CASE WHEN study='Base' THEN {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:vis.visit_number,study_id:study} END as prop order by duration, study
            with duration, collect(distinct prop) as props
            with duration, [x in range(0,size(props)-1,1) |
            CASE WHEN size(props)=2 and not props[0].visit_number = props[1].visit_number 
            THEN apoc.create.vNode([ \\\"Visit \\\"],
            {visit_number:( \\\"<p style='color:green;'>Base:  \\\" + props[0].visit_number +  \\\"</p><p style='color:red;'</p> \\\"),
                        duration:toInteger(duration),
                        visit_name:( \\\"<p style='color:green;'>Base:  \\\" + props[0].visit_name),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        }) 
                        ELSE 
                        CASE WHEN size(props)=2 and props[0].visit_number = props[1].visit_number
                        THEN apoc.create.vNode([ \\\"Visit \\\"],
                        {visit_number: props[0].visit_number,
                        duration:toInteger(duration),
                        visit_name:substring(props[x].study_id,0,4)+': '+props[0].visit_name,
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        }) ELSE 
                        CASE WHEN size(props)<2 and props[x].study_id='Base' 
                            THEN apoc.create.vNode([ \\\"Visit \\\"],
                        {visit_number:( \\\"<p style='color:green;'>Base:  \\\" + props[x].visit_number +  \\\"</p><p style='color:red;'>Comp: Null </p> \\\"),
                        duration:toInteger(duration),
                        visit_name:( \\\"<p style='color:green;'>Base:  \\\" + props[x].visit_name +  \\\"</p><p style='color:red;'>Comp: Null </p> \\\"),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        })  ELSE
                        CASE WHEN size(props)<2 and props[x].study_id='Compare' 
                            THEN apoc.create.vNode([ \\\"Visit \\\"],
            {visit_number:( \\\"<p style='color:green;'>Base: Null </p><p style='color:red;'>Comp: \\\" + props[x].visit_number +  \\\"</p> \\\"),
                        duration:toInteger(duration),
                        visit_name:(\\\"<p style='color:green;'>Base: Null</p><p style='color:red;'>Comp: \\\" + props[x].visit_name),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        })END END END END] as v_visits
            with distinct duration, v_visits
            UNWIND v_visits as v_visit
            with duration, apoc.any.property(v_visit,'study_id') as study, v_visit
            with study, collect(duration) as durations, collect(v_visit) as v_visits
            with study, durations, v_visits, [n in RANGE(0,size(v_visits)-2) | apoc.create.vRelationship(v_visits[n], \\\"FOLLOWS \\\",{type: \\\"logical \\\"},v_visits[n+1]) ]as v_rels, range(0,size(v_visits)-1,1) AS coll_size 
            with study, durations, v_visits,v_rels, coll_size 
            UNWIND coll_size AS idx
            WITH  study, durations[idx] as duration,
            v_visits[idx] as v_visit, v_rels[idx] as v_rel
            return v_visit,v_rel\",
 visitmap['Base']='FALSE' and visitmap['Compare']='TRUE', 
            \"with $t as t
            UNWIND t as s 
            with s, CASE when id(s)=toInteger($neodash_studyb) then 'Compare' END as study
            optional match (s)-[:HAS_STUDY_VISIT]->(vis)
            optional match(vis)-[:HAS_STUDY_DURATION_DAYS]->(dur_day_root:StudyDurationDaysRoot)-[:HAS_VERSION]->(dur_days:StudyDurationDaysValue)
            optional match(vis)-[:HAS_STUDY_DURATION_WEEKS]->(dur_wk_root:StudyDurationWeeksRoot)-[:HAS_VERSION]->(dur_week:StudyDurationWeeksValue)
            optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
            with s, study, vis, dur_days, vis_name order by id(s), vis.visit_number
            with distinct s, study, dur_days.value as duration,vis, 
            CASE WHEN study='Base' THEN {duration:dur_days.value,visit_name:vis_name.name+'; Day: '+toString(toInteger(dur_days.value)), endDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), startDate:date($neodash_sstdtc)+Duration({days:(dur_days.value)}), visit_number:vis.visit_number,study_id:study} END as prop order by duration, study
            with duration, collect(distinct prop) as props
            with duration, [x in range(0,size(props)-1,1) |
            CASE WHEN size(props)=2 and not props[0].visit_number = props[1].visit_number 
            THEN apoc.create.vNode([ \\\"Visit \\\"],
            {visit_number:( \\\"<p style='color:green;'>Base:  \\\" + props[0].visit_number +  \\\"</p><p style='color:red;'</p> \\\"),
                        duration:toInteger(duration),
                        visit_name:( \\\"<p style='color:green;'>Base:  \\\" + props[0].visit_name),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        }) 
                        ELSE 
                        CASE WHEN size(props)=2 and props[0].visit_number = props[1].visit_number
                        THEN apoc.create.vNode([ \\\"Visit \\\"],
                        {visit_number: props[0].visit_number,
                        duration:toInteger(duration),
                        visit_name:substring(props[x].study_id,0,4)+': '+props[0].visit_name,
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        }) ELSE 
                        CASE WHEN size(props)<2 and props[x].study_id='Base' 
                            THEN apoc.create.vNode([ \\\"Visit \\\"],
                        {visit_number:( \\\"<p style='color:green;'>Base:  \\\" + props[x].visit_number +  \\\"</p><p style='color:red;'>Comp: Null </p> \\\"),
                        duration:toInteger(duration),
                        visit_name:( \\\"<p style='color:green;'>Base:  \\\" + props[x].visit_name +  \\\"</p><p style='color:red;'>Comp: Null </p> \\\"),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        })  ELSE
                        CASE WHEN size(props)<2 and props[x].study_id='Compare' 
                            THEN apoc.create.vNode([ \\\"Visit \\\"],
            {visit_number:( \\\"<p style='color:green;'>Base: Null </p><p style='color:red;'>Comp: \\\" + props[x].visit_number +  \\\"</p> \\\"),
                        duration:toInteger(duration),
                        visit_name:(\\\"<p style='color:green;'>Base: Null</p><p style='color:red;'>Comp: \\\" + props[x].visit_name),
                        startDate:date($neodash_sstdtc)+Duration({days:(duration)}), 
                        endDate:date($neodash_sstdtc)+Duration({days:(duration)}),
                        study_id:props[x].study_id,
                        visit_label:substring(props[x].study_id,0,4)+': '+props[x].visit_name
                        })END END END END] as v_visits
            with distinct duration, v_visits
            UNWIND v_visits as v_visit
            with duration, apoc.any.property(v_visit,'study_id') as study, v_visit
            with study, collect(duration) as durations, collect(v_visit) as v_visits
            with study, durations, v_visits, [n in RANGE(0,size(v_visits)-2) | apoc.create.vRelationship(v_visits[n], \\\"FOLLOWS \\\",{type: \\\"logical \\\"},v_visits[n+1]) ]as v_rels, range(0,size(v_visits)-1,1) AS coll_size 
            with study, durations, v_visits,v_rels, coll_size 
            UNWIND coll_size AS idx
            WITH  study, durations[idx] as duration,
            v_visits[idx] as v_visit, v_rels[idx] as v_rel
            return v_visit,v_rel\"],
            \"RETURN NULL as v_visit, NULL as v_rel\",{t:$t,neodash_studya:$studya,neodash_studyb:$studyb,neodash_sstdtc:$sstdtc}) YIELD value 
with distinct value
MATCH (n:Library) where value.v_visit is not null
return distinct value.v_visit as v_visit,value.v_rel as v_rel"  
,
"RETURN NULL as v_visit, NULL as v_rel",{t:st,sstdtc:$neodash_sstdtc, studya:$neodash_studya, studyb:$neodash_studyb}) YIELD value 
with distinct value
MATCH (n:Library) where value.v_visit is not null
return distinct value.v_visit as v_visit, value.v_rel as v_rel