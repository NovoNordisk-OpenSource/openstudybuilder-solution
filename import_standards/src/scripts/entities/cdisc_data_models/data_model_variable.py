class DataModelVariable:
    def __init__(self, href: str):
        self.href = href

    def set_attributes(
        self,
        name: str,
        title: str,
        label: str,
        description: str,
        ordinal: str,
        role: str,
        notes: str,
        variable_c_code: str,
        usage_restrictions: str,
        examples: "list[str]",
        value_list: str,
        described_value_domain: str,
        qualifies_variables: "list[str]",
        role_description: str,
        simple_datatype: str,
        length: str,
        definition: str,
        implementation_notes: str,
        mapping_instructions: str,
        prompt: str,
        question_text: str,
        completion_instructions: str,
        core: str,
        codelists: "list[str]",
        implements_variables: "list[str]",
        mapping_targets: "list[str]",
        prior_version: str,
        analysis_variable_set: str,
    ):
        self.name: str = name
        self.title: str = title
        self.label: str = label
        self.description: str = description if description else definition
        self.ordinal: str = ordinal
        self.role: str = role
        self.role_description: str = role_description
        self.simple_datatype: str = simple_datatype
        self.length: str = length
        self.codelists: list[str] = codelists
        self.prior_version: str = prior_version

        # SDTM & SDTMIG specific
        self.notes: str = notes
        self.variable_c_code: str = variable_c_code
        self.usage_restrictions: str = usage_restrictions
        self.examples: list[str] = examples
        self.value_list: str = value_list
        self.described_value_domain: str = described_value_domain
        self.qualifies_variables: list[str] = qualifies_variables

        # CDASH & CDASHIG specific
        self.implementation_notes: str = implementation_notes
        self.mapping_instructions: str = mapping_instructions
        self.prompt: str = prompt
        self.question_text: str = question_text
        self.completion_instructions: str = completion_instructions

        # IG specific
        self.core: str = core
        self.implements_variables: list[str] = implements_variables

        # CDASHIG specific
        self.mapping_targets: list[str] = mapping_targets

        # ADaM specific
        self.analysis_variable_set: str = analysis_variable_set
