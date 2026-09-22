FEATURE_FLAGS = """
UNWIND [{sn:1, properties:{name:"feature_flag_1", description: "description", enabled: true}}, {sn: 2, properties:{name:"feature_flag_2", description: "description", enabled: false}}] AS row
MERGE (n:FeatureFlag{sn: row.sn}) SET n += row.properties;
"""

TEST_DATA = FEATURE_FLAGS
