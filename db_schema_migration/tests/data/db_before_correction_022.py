# Test data for correction 022: remove lonely unused _Neodash_Dashboard node
#
# - Unused row matching PROD identifiers (no relationships)
# - Control dashboard with different uuid (must survive)

TEST_DATA = """
CREATE (unused:_Neodash_Dashboard {
    uuid: '6b288611-7f89-482c-a850-b34b19cf6ebb',
    title: 'External Data File Specifications',
    user: 'devops_adm',
    date: '2025-10-05 13:20:42 +0000',
    version: '1.0',
    content: '{}'
});
CREATE (keep:_Neodash_Dashboard {
    uuid: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    title: 'Other Dashboard',
    user: 'other_user',
    date: '2025-01-01 00:00:00 +0000',
    version: '1.0',
    content: '{}'
})
"""
