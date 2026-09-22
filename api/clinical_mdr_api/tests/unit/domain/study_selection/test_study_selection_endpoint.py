import datetime
import random
import unittest
from copy import copy

from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common import exceptions

uid_list = [
    "uid_endpoint",
    "uid_study_objective",
    "uid_timeframe",
    "uid_objective",
    "uid_level",
]
level = [None, "", "Primary", "Secondary"]


# Simple callback to see if string exist in list(mock DB)
def _check_uid_exists_callback(uid: str) -> bool:
    if uid in uid_list:
        return True
    return False


def create_random_valid_vo(
    selection_uid: str | None = None, endpoint_order: int = 2
) -> StudySelectionEndpointVO:
    if selection_uid is None:
        selection_uid = random_str()
    uid_endpoint = random_str()
    uid_timeframe = random_str()
    uid_study_objective = "uid_study_objective_000001"
    uid_level = random_str()
    uid_sublevel = random_str()
    start_datetime = datetime.datetime.now(datetime.timezone.utc)
    uid_list.extend(
        [uid_study_objective, uid_timeframe, uid_endpoint, uid_level, uid_sublevel]
    )
    study_selection_endpoint_vo = StudySelectionEndpointVO.from_input_values(
        endpoint_level_order=endpoint_order,
        endpoint_uid=uid_endpoint,
        endpoint_level_uid=uid_level,
        endpoint_sublevel_uid=uid_sublevel,
        unit_separator=random_str(),
        study_objective_uid=uid_study_objective,
        timeframe_uid=uid_timeframe,
        endpoint_units=[
            {"uid": random_str(), "name": random_str()},
            {"uid": random_str(), "name": random_str()},
        ],
        start_date=start_datetime,
        author_id=random_str(),
        study_selection_uid=selection_uid,
        timeframe_version="1.0",
        endpoint_version="2.0",
    )
    study_selection_endpoint_vo.validate(_check_uid_exists_callback)
    return study_selection_endpoint_vo


# test StudySelectionObjectivesVO
class TestStudySelectionEndpointVO(unittest.TestCase):
    def test__validate__success(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            [
                "uid_endpoint",
                "uid_level",
                None,
                "uid_study_objective",
                random_str(),
                "uid_timeframe",
                [{"uid": random_str(), "name": random_str()}],
                "uid_objective",
                start_datetime,
                "0.3",
                "0.4",
            ],
            [
                "uid_endpoint ",
                "uid_level",
                random_str(),
                "uid_study_objective ",
                random_str(),
                "uid_timeframe ",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                "uid_objective ",
                start_datetime,
                "1.3",
                "0.4",
            ],
            [
                " uid_endpoint",
                "uid_level",
                random_str(),
                " uid_study_objective",
                random_str(),
                " uid_timeframe",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                " uid_objective",
                start_datetime,
                "2.3",
                "1.4",
            ],
            [
                " uid_endpoint ",
                "uid_level",
                None,
                " uid_study_objective ",
                random_str(),
                " uid_timeframe ",
                [{"uid": random_str(), "name": random_str()}],
                " uid_objective ",
                start_datetime,
                "2.0",
                "1.0",
            ],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=test_tuple[0],
                    endpoint_level_order=2,
                    endpoint_level_uid=test_tuple[1],
                    endpoint_sublevel_uid=test_tuple[1],
                    unit_separator=test_tuple[2],
                    study_objective_uid=test_tuple[3],
                    timeframe_uid=test_tuple[5],
                    endpoint_units=test_tuple[6],
                    start_date=test_tuple[8],
                    study_selection_uid="dummy",
                    endpoint_version=test_tuple[9],
                    timeframe_version=test_tuple[10],
                    author_id="Initials",
                )
                study_selection_endpoint.validate(
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                )

    def test__validate__failure(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            [
                "wrong_endpoint_uid",
                random_str(),
                random_str(),
                "uid_study_objective",
                random_str(),
                "uid_timeframe",
                [{"uid": random_str()}, {"uid": random_str()}],
                "uid_objective",
                start_datetime,
            ],
            [
                "uid_endpoint",
                random_str(),
                random_str(),
                "wrong_study_objective_uid",
                random_str(),
                "uid_timeframe",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                "uid_objective",
                start_datetime,
            ],
            [
                "uid_endpoint",
                random_str(),
                random_str(),
                "uid_study_objective",
                random_str(),
                "wrong_timeframe",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                "uid_objective",
                start_datetime,
            ],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=test_tuple[0],
                    endpoint_level_order=2,
                    endpoint_level_uid=test_tuple[1],
                    endpoint_sublevel_uid=test_tuple[1],
                    unit_separator=test_tuple[2],
                    study_objective_uid=test_tuple[3],
                    timeframe_uid=test_tuple[5],
                    endpoint_units=test_tuple[6],
                    start_date=test_tuple[8],
                    study_selection_uid="dummy",
                    endpoint_version="1.0",
                    timeframe_version="2.0",
                    author_id="Initials",
                )
                with self.assertRaises(exceptions.BusinessLogicException):
                    study_selection_endpoint.validate(
                        _check_uid_exists_callback,
                        _check_uid_exists_callback,
                        _check_uid_exists_callback,
                        _check_uid_exists_callback,
                    )

    def test__validate__success_unit_separator_states(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            [
                "uid_endpoint",
                "uid_level",
                None,
                "uid_study_objective",
                random_str(),
                "uid_timeframe",
                [{"uid": random_str(), "name": random_str()}],
                None,
                start_datetime,
            ],
            [
                "uid_endpoint ",
                "uid_level",
                None,
                "uid_study_objective ",
                random_str(),
                "uid_timeframe ",
                None,
                ["uid_objective "],
                start_datetime,
            ],
            [
                " uid_endpoint",
                "uid_level",
                "and",
                " uid_study_objective",
                random_str(),
                " uid_timeframe",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                [" uid_objective", "unit"],
                start_datetime,
            ],
            [
                " uid_endpoint ",
                "uid_level",
                "or",
                " uid_study_objective ",
                random_str(),
                " uid_timeframe ",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                [" uid_objective", "unit"],
                start_datetime,
            ],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=test_tuple[0],
                    endpoint_level_uid=test_tuple[1],
                    endpoint_sublevel_uid=test_tuple[1],
                    endpoint_level_order=None,
                    unit_separator=test_tuple[2],
                    study_objective_uid=test_tuple[3],
                    timeframe_uid=test_tuple[5],
                    endpoint_units=test_tuple[6],
                    start_date=test_tuple[8],
                    study_selection_uid="dummy",
                    endpoint_version="1.0",
                    timeframe_version="2.0",
                    author_id="Initials",
                )
                study_selection_endpoint.validate(
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                )

    def test__validate__failure__unit_separator_states(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            [
                "uid_endpoint",
                "uid_level_test",
                "and",
                "uid_study_objective",
                random_str(),
                "uid_timeframe",
                None,
                "uid_objective",
                start_datetime,
            ],
            [
                "uid_endpoint",
                "uid_level_test",
                "or",
                "uid_study_objective",
                random_str(),
                "uid_timeframe",
                [{"uid": random_str(), "name": random_str()}],
                "uid_objective",
                start_datetime,
            ],
            [
                "uid_endpoint ",
                "uid_level_test",
                None,
                "uid_study_objective ",
                random_str(),
                "uid_timeframe ",
                [
                    {"uid": random_str()},
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str()},
                ],
                "uid_objective ",
                start_datetime,
            ],
            [
                "uid_endpoint ",
                "uid_level_test",
                None,
                "uid_study_objective ",
                random_str(),
                "uid_timeframe ",
                [
                    {"uid": random_str(), "name": random_str()},
                    {"uid": random_str(), "name": random_str()},
                ],
                "uid_objective ",
                start_datetime,
            ],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=test_tuple[0],
                    endpoint_level_uid=test_tuple[1],
                    endpoint_sublevel_uid=test_tuple[1],
                    endpoint_level_order=2,
                    unit_separator=test_tuple[2],
                    study_objective_uid=test_tuple[3],
                    timeframe_uid=test_tuple[5],
                    endpoint_units=test_tuple[6],
                    start_date=test_tuple[8],
                    study_selection_uid="dummy",
                    endpoint_version="1.0",
                    timeframe_version="2.0",
                    author_id="Initials",
                )
                with self.assertRaises(exceptions.ValidationException):
                    study_selection_endpoint.validate(
                        _check_uid_exists_callback,
                        _check_uid_exists_callback,
                        _check_uid_exists_callback,
                        _check_uid_exists_callback,
                    )


class TestStudySelectionEndpointsAR(unittest.TestCase):
    def test__add_new_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                study_selection_endpoint_ar.repository_closure_data = copy(
                    test_tuple[1]
                )
                self.assertEqual(
                    len(test_tuple[1]),
                    len(study_selection_endpoint_ar.study_endpoints_selection),
                )

                study_selection_endpoint_ar.add_endpoint_selection(
                    create_random_valid_vo(),
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                )

                self.assertEqual(
                    len(test_tuple[1]) + 1,
                    len(study_selection_endpoint_ar.study_endpoints_selection),
                )

    def test__get_specific_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_endpoint_ar.add_endpoint_selection(
                    new_vo,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                )

                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                self.assertEqual(len(test_tuple[1]) + 1, order)
                with self.assertRaises(exceptions.NotFoundException):
                    study_selection_endpoint_ar.get_specific_endpoint_selection(
                        "wrong uid"
                    )

    def test__remove_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    _,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                # remove the vo
                study_selection_endpoint_ar.remove_endpoint_selection(
                    new_vo.study_selection_uid
                )

                # assert that it is no longer in the AR
                with self.assertRaises(exceptions.NotFoundException):
                    study_selection_endpoint_ar.get_specific_endpoint_selection(
                        new_vo.study_selection_uid
                    )

    def test__update_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    _,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                # create a updated vo
                updated_vo = create_random_valid_vo(
                    selection_uid=new_vo.study_selection_uid
                )

                # # update the selection
                study_selection_endpoint_ar.update_selection(
                    updated_study_endpoint_selection=updated_vo,
                    study_objective_exist_callback=_check_uid_exists_callback,
                    endpoint_exist_callback=_check_uid_exists_callback,
                    timeframe_exist_callback=_check_uid_exists_callback,
                    ct_term_exists_callback=_check_uid_exists_callback,
                )

                # assert that the two vo are not the same
                self.assertFalse(new_vo is updated_vo)

                # assert updated has updated to the new vo but kept the uid
                (
                    selection,
                    _,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(selection, updated_vo)

    def test__reorder_vo(self):
        test_tuples = [
            (random_str(), [create_random_valid_vo(random_str(), 2)]),
            (
                random_str(),
                [
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                ],
            ),
            (
                random_str(),
                [
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo(random_str(), 2)
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                new_order = random.randrange(1, len(test_tuple[1]) + 2, 1)
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=new_order
                )

                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_order, order)

                # assert that the selection is put on the end when the order is higher than the amount of selections in total
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=999
                )
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )

                self.assertEqual(
                    len(study_selection_endpoint_ar.study_endpoints_selection), order
                )

                # assert that the selection is put in front when the order is lower than 1
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=-99
                )
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(1, order)

    def test__update_vo_with_new_study_objective(self):
        test_tuples = [
            (random_str(), [create_random_valid_vo(random_str(), 2)]),
            (
                random_str(),
                [
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                ],
            ),
            (
                random_str(),
                [
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo(random_str(), 2)
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                new_order = random.randrange(1, len(test_tuple[1]) + 2, 1)
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=new_order
                )

                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_order, order)

                # assert that the selection is put on the end when the order is higher than the amount of selections in total
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=999
                )
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )

                self.assertEqual(
                    len(study_selection_endpoint_ar.study_endpoints_selection), order
                )

                # assert that the selection is put in front when the order is lower than 1
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=-99
                )
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(1, order)

    def test__update_vo_with_new_endpoint_order(self):
        test_tuples = [
            (random_str(), [create_random_valid_vo(random_str(), 2)]),
            (
                random_str(),
                [
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                ],
            ),
            (
                random_str(),
                [
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                    create_random_valid_vo(random_str(), 2),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo(random_str(), 2)
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                new_order = random.randrange(1, len(test_tuple[1]) + 2, 1)
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=new_order
                )

                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_order, order)

                # assert that the selection is put on the end when the order is higher than the amount of selections in total
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=999
                )
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )

                self.assertEqual(
                    len(study_selection_endpoint_ar.study_endpoints_selection), order
                )

                # assert that the selection is put in front when the order is lower than 1
                study_selection_endpoint_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=-99
                )
                (
                    selection,
                    order,
                ) = study_selection_endpoint_ar.get_specific_endpoint_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(1, order)

    def test__validate(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # Check that the AR is valid:
                study_selection_endpoint_ar.validate()

    def test__validate_failure_having_same_endpoint(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_endpoint_ar = (
                    StudySelectionEndpointsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_endpoints_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_endpoint_ar.add_endpoint_selection(new_vo)

                # validate we cannot add the same v0 again
                with self.assertRaises(exceptions.AlreadyExistsException):
                    study_selection_endpoint_ar.add_endpoint_selection(new_vo)
                    study_selection_endpoint_ar.validate()
