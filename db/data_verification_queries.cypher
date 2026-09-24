// CodeLists (current version) by Library and ordered by CTModel name
MATCH (l:Library)-[:HAS_MODEL]->(m:CTModel)-[:CURRENT]->(p:CTPackage)-[:HAS_CODE_LIST]->(c:CTCodeList)
RETURN l.name, m.name, p.id, c.id, c.name, c.submissionValue order by m.name LIMIT 100

// Find Current CTPackage (ordered by the number of Terms in it)
MATCH (m:CTModel)-[:CURRENT]->(p:CTPackage)-[:HAS_CODE_LIST]->(c:CTCodeList)-[:HAS_TERM]->()
RETURN m.name, p.name, c.id, c.preferredTerm, count(*) AS cnt ORDER BY cnt DESC LIMIT 10

// Find Current CTTerm (ordered by the number of CodeLists it belongs to)
MATCH (:CTTermRoot)-[:CURRENT]->(t:CTTerm)<-[:HAS_TERM]-()
RETURN t.id, t.preferredTerm, count(*) AS cnt ORDER BY cnt DESC LIMIT 10

// Look at CTTerm nodes for a given CTCodeList
MATCH (c:CTCodeList{id:"C67154-SDTM CT 2018-12-21"})-[:HAS_TERM]->(t:CTTerm)
RETURN c.id, c.preferredTerm, t.id, t.preferredTerm ORDER BY c.id ASC LIMIT 10

// Look at CTCodeList nodes for a given CTTerm
MATCH (t:CTTerm{id:"C124281-SDTM CT 2020-06-26"})<-[:HAS_TERM]-(c:CTCodeList)
RETURN c.id, c.preferredTerm ORDER BY c.id ASC LIMIT 10

// Find the CTCodeListRoot given a CTCodeList
MATCH (tv:CTCodeList{id:"C67154-SDTM CT 2018-12-21"})<-[:CURRENT|PREVIOUS*1..50]-(rt:CTCodeListRoot)
RETURN rt

// Find the CTTermRoot given a CTTerm
MATCH (tv:CTTerm{id:"C124281-SDTM CT 2020-06-26"})<-[:CURRENT|PREVIOUS*1..50]-(rt:CTTermRoot)
RETURN rt


// Find the current CTTerm for a CTTermRoot
MATCH p = (rt:CTTermRoot{id: "C165858"})-[:CURRENT]->(:CTTerm)
RETURN p


// Have synonymes changed between CTTerms?
MATCH p=(s2:Synonym)<-[:TERM_SYNONYM]-(v2:CTTerm)-[:PREVIOUS]->(v1:CTTerm)-[:TERM_SYNONYM]->(s1:Synonym)
WHERE NOT ( (s1)<-[:TERM_SYNONYM]-(v2) AND (v1)-[:TERM_SYNONYM]->(s2) )
RETURN p LIMIT 1 // YES


// Have CodeList Terms changed between CTCodeList and previously released CTCodeList?
MATCH p=(c2:CTTerm)<-[:HAS_TERM]-(v2:CTCodeList)-[:PREVIOUS]->(v1:CTCodeList)-[:HAS_TERM]->(c1:CTTerm)
WHERE NOT ( (c2)-[:PREVIOUS]->() AND (c1)<-[:PREVIOUS]-() )
RETURN p LIMIT 1 // YES


// Is there a newer version for a CTTerm
MATCH p=(:CTTerm{id:"C165858-ADaM CT 2019-12-20"})<-[:PREVIOUS*1..10]-(:CTTerm)
RETURN p // YES


// The most used CodeList Synonyms (in current version)
MATCH (:CTCodeListRoot)-[:CURRENT]->(c:CTCodeList)-[:CODE_LIST_SYNONYM]->(s:Synonym)
RETURN s.name, count(*) AS cnt ORDER BY cnt DESC LIMIT 10


// The most used Term Synonyms (in current version)
MATCH (:CTCodeListRoot)-[:CURRENT]->(c:CTCodeList)-[:HAS_TERM]->(tv:CTTerm)-[:TERM_SYNONYM]->(s:Synonym)
RETURN s.name, count(*) AS cnt ORDER BY cnt DESC LIMIT 10


// Diff two versions of a CTCodeList
MATCH (t:CTCodeList)-[:HAS_TERM]->(tv:CTTerm) WHERE t.id in ["C67152-SDTM CT 2020-03-27", "C67152-SDTM CT 2020-06-26"]
RETURN 
t.id,
size( (t)-[:HAS_TERM]->() ) AS numberOfTerms,
size( (t)-[:CODE_LIST_SYNONYM]->() ) AS numberOfSynonymes,
collect(tv.submissionValue) as terms

// What CTTerms differ CTCodeList
MATCH (t:CTCodeList)-[:HAS_TERM]->(tv:CTTerm) WHERE t.id in ["C67152-SDTM CT 2020-03-27", "C67152-SDTM CT 2020-06-26"]
WITH t, collect(tv.submissionValue) as terms order by t.id
WITH collect(terms) as termsArray
RETURN  // [0] = old [1] = new as we are ordering asc by id that contains the iso date
    apoc.coll.intersection(termsArray[0], termsArray[1]) as InCommon,
    apoc.coll.subtract(termsArray[0], termsArray[1]) as Removed,
    apoc.coll.subtract(termsArray[1], termsArray[0]) as Added


// Race CTCodeList over time
MATCH (:CTCodeListRoot{id:"C74457"})-[:CURRENT|PREVIOUS*1..100]->(c:CTCodeList)-[:HAS_TERM]->(t:CTTerm)
WITH c,t order by c.id desc, t.preferredTerm asc
RETURN c.id, c.submissionValue, collect(t.preferredTerm)



// Diff two versions of a CTTerm
MATCH (t:CTTerm)-[:TERM_SYNONYM]->(s:Synonym) WHERE t.id in ["C158155-ADaM CT 2019-12-20", "C158155-ADaM CT 2020-03-27"]
RETURN 
t.id,
size( (t)<-[:HAS_TERM]-() ) AS numberCodeLists,
size( (t)-[:TERM_SYNONYM]->() ) AS numberOfSynonymes,
collect(s.name) as synonymes


