from enum import IntEnum


class TutorialStage(IntEnum):
    BEFORE_FORAGE = 1
    NO_RESOURCES = 2
    RESOURCES_AVAILABLE = 3
    INSPECT_AVAILABLE = 4
    GENE_HELPER_TEXT_CLICKED = 5

class CurrentTutorialStage:
    current_tutorial_stage = TutorialStage.BEFORE_FORAGE