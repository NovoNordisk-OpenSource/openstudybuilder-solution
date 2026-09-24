import datetime
import random
import unittest
from copy import copy

from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str
from common import exceptions

uid_list = ["uid_1", "uid_2", "uid_3", "ctterm_1", "ctterm_2"]
obj_level = [None, "", "Primary", "Secondary"]


# Simple callback to see if string exist in list(mock DB)
def _check_uid_exists_callback(uid: str) -> bool:
    if uid in uid_list:
        return True
    return False


def create_random_valid_vo(
    selection_uid: str | None = None, objective_order: int = 2
) -> StudySelectionObjectiveVO:
    if selection_uid is None:
        selection_uid = random_str()
    uid = random_str()
    uid2 = random_str()
    version = "1.1"
    uid_list.extend([uid, uid2])
    study_selection_objective_vo = StudySelectionObjectiveVO.from_input_values(
        objective_uid=uid,
        study_selection_uid=selection_uid,
        objective_version=version,
        objective_level_uid=uid2,
        objective_level_order=objective_order,
        start_date=datetime.datetime.now(datetime.timezone.utc),
        author_id=random_str(),
    )
    study_selection_objective_vo.validate(
        _check_uid_exists_callback, _check_uid_exists_callback
    )
    return study_selection_objective_vo


# test StudySelectionObjectivesVO
class TestStudySelectionObjectiveVO(unittest.TestCase):
    def test__validate__success(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            ["uid_1", "ctterm_1", start_datetime, "1.0", "unknown-user", 1],
            [" uid_2", "ctterm_2", start_datetime, " 2.0 ", "unknown-user", 2],
            ["uid_3 ", None, start_datetime, " 3.0", "unknown-user", None],
            [" uid_3 ", "", start_datetime, "4.0", "unknown-user", None],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective = StudySelectionObjectiveVO.from_input_values(
                    study_selection_uid=random_str(),
                    objective_version=test_tuple[3],
                    objective_uid=test_tuple[0],
                    objective_level_uid=test_tuple[1],
                    objective_level_order=test_tuple[5],
                    start_date=test_tuple[2],
                    author_id=test_tuple[4],
                )
                study_selection_objective.validate(
                    _check_uid_exists_callback, _check_uid_exists_callback
                )

    def test__validate__failure(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            ["uid_1_200", "uid_1", start_datetime, "1.0", "unknown-user", None],
            ["", None, start_datetime, "2.0", "unknown-user", 1],
            ["____////", "", start_datetime, "3.0", "unknown-user", 3],
            ["uid_1", "Primary", start_datetime, "3.0", "unknown-user", 1],
            ["uid_1", "_uid_1", start_datetime, "3.0", "unknown-user", 2],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective = StudySelectionObjectiveVO.from_input_values(
                    study_selection_uid=random_str(),
                    objective_uid=test_tuple[0],
                    objective_level_uid=test_tuple[1],
                    objective_level_order=test_tuple[5],
                    start_date=test_tuple[2],
                    author_id=test_tuple[4],
                    objective_version=test_tuple[3],
                )
                with self.assertRaises(exceptions.BusinessLogicException):
                    study_selection_objective.validate(
                        _check_uid_exists_callback, _check_uid_exists_callback
                    )


class TestStudySelectionObjectivesAR(unittest.TestCase):
    def test__add_new_vo(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                study_selection_objective_ar.repository_closure_data = copy(
                    test_tuple[1]
                )
                self.assertEqual(
                    len(test_tuple[1]),
                    len(study_selection_objective_ar.study_objectives_selection),
                )

                study_selection_objective_ar.add_objective_selection(
                    create_random_valid_vo()
                )

                self.assertEqual(
                    len(test_tuple[1]) + 1,
                    len(study_selection_objective_ar.study_objectives_selection),
                )

    def test__get_specific_vo(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_objective_ar.add_objective_selection(new_vo)

                (
                    selection,
                    order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                self.assertEqual(len(test_tuple[1]) + 1, order)
                with self.assertRaises(exceptions.NotFoundException):
                    study_selection_objective_ar.get_specific_objective_selection(
                        "wrong uid"
                    )

    def test__remove_vo(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_objective_ar.add_objective_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    _,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                # remove the vo
                study_selection_objective_ar.remove_objective_selection(
                    new_vo.study_selection_uid
                )

                # assert that it is no longer in the AR
                with self.assertRaises(exceptions.NotFoundException):
                    study_selection_objective_ar.get_specific_objective_selection(
                        new_vo.study_selection_uid
                    )

    def test__update_vo(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_objective_ar.add_objective_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    _,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                # create new vo with different objective uid and objective level, but same selection uid
                new_v1 = create_random_valid_vo(new_vo.study_selection_uid)
                study_selection_objective_ar.update_selection(
                    updated_study_objective_selection=new_v1,
                    objective_exist_callback=_check_uid_exists_callback,
                )

                # assert that the selection data is changed
                self.assertFalse(
                    new_v1.objective_level_uid is new_vo.objective_level_uid
                )
                self.assertFalse(new_v1.objective_uid is new_vo.objective_uid)

                # assert that the selection data is the correct data
                (
                    selection,
                    _,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(
                    selection.objective_level_uid, new_v1.objective_level_uid
                )
                self.assertEqual(selection.objective_uid, new_v1.objective_uid)

    def test__update_vo_with_new_objective_order(self):
        test_tuples = [
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                study_selection_uid = random_str()
                new_vo = create_random_valid_vo(study_selection_uid, 1)
                study_selection_objective_ar.add_objective_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    original_order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                self.assertEqual(original_order, 1)

                # create new vo with different objective uid and objective level, but same selection uid
                new_v1 = create_random_valid_vo(new_vo.study_selection_uid, 3)
                study_selection_objective_ar.update_selection(
                    updated_study_objective_selection=new_v1,
                    objective_exist_callback=_check_uid_exists_callback,
                )

                # assert that the selection data is changed
                self.assertFalse(
                    new_v1.objective_level_uid is new_vo.objective_level_uid
                )
                self.assertFalse(new_v1.objective_uid is new_vo.objective_uid)

                # assert that the selection data is the correct data
                (
                    selection,
                    order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(
                    selection.objective_level_uid, new_v1.objective_level_uid
                )
                self.assertEqual(selection.objective_uid, new_v1.objective_uid)

                self.assertGreater(order, original_order)

    def test__reorder_vo(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_objective_ar.add_objective_selection(new_vo)

                # ensure it is still there
                (
                    selection,
                    order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                new_order = random.randrange(1, len(test_tuple[1]) + 2, 1)
                study_selection_objective_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid,
                    new_order=new_order,
                    author_id=AUTHOR_ID,
                )

                (
                    selection,
                    order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_order, order)

                # assert that the selection is put on the end when the order is higher than the amount of selections in total
                study_selection_objective_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid,
                    new_order=999,
                    author_id=AUTHOR_ID,
                )
                (
                    selection,
                    order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )

                self.assertEqual(
                    len(study_selection_objective_ar.study_objectives_selection), order
                )

                # assert that the selection is put in front when the order is lower than 1
                study_selection_objective_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid,
                    new_order=-99,
                    author_id=AUTHOR_ID,
                )
                (
                    selection,
                    order,
                ) = study_selection_objective_ar.get_specific_objective_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(1, order)

    def test__validate(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_objective_ar.add_objective_selection(new_vo)

                # Check that the AR is valid:
                study_selection_objective_ar.validate()

    def test__validate_failure_having_same_objective(self):
        test_tuples = [
            (random_str(), [], 0),
            (random_str(), [create_random_valid_vo()], 0),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()], 0),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
                0,
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_objective_ar = (
                    StudySelectionObjectivesAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_objectives_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_objective_ar.add_objective_selection(new_vo)

                # validate we cannot add the same v0 again
                with self.assertRaises(exceptions.AlreadyExistsException):
                    study_selection_objective_ar.add_objective_selection(new_vo)
                    study_selection_objective_ar.validate()
