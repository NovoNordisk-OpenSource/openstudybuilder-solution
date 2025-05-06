# Study Visits

Study visits are handled in `define study/Study Structure/Study visits tab`.

Below you will find a walk-through of the visit setup process and how you work with visits in OpenStudyBuilder.

![Overview of possible actions for managing visits](~@source/images/user_guides/guide_visits_01.png)
Figure 1: Overview of possible actions for managing visits


## Adding Visits

The following visit scheduling types are available:

Visit scheduling type (visit class) | Description
-- | --
Scheduled visit | A visit with a planned timing. Scheduled visits can be of the following subclasses: <br>- Single visit<br>- Anchor visit in visit group<br>- Additional sub-visit<br>- Repeating visit
Unscheduled visit | A technical visit, where data can be put for unscheduled data collection, e.g., extra lab samples
Non-visit | A technical visit for non-visit data collection
Special Visit | An event-driven visit, like early treatment discontinuation or repeated visits for observational studies
Manually defined visit | A visit with Visit name, Visit short name as well as Visit number and Unique visit number defined fully manually by the user

> Note: The selected scheduling type of the visit is displayed in the table columns as visit class and visit subclass.


## Planned Visit Schedule

The planned visit schedule is typically using the visit scheduling type (class) 'scheduled visit' and subclass 'Single visit'. You will need an epoch you can assign the visit to.

1. For the first visit, you will receive a warning that no global anchor visit is identified yet unless you dedicate the first visit as Global anchor visit. The global anchor visit is the reference visit that should be used the calculate timing from, e.g., the randomization visit. In general, the visit table holds different timing formats to meet different needs.

1. You can refer to the global anchor visit even though you have not marked any visit as global anchor visit yet, if you know the relative timing between visits (see figure 2)

    ![Assign the first visit with relative timing to global anchor as -14 days](~@source/images/user_guides/guide_visits_02.jpg)

    Figure 2: Example - Assign the first visit with relative timing to global anchor as -14 days

1. When you have created the first visit, it is visible in the visit table. If you scroll to the right, you can see the different timing variables that can be used for Schedule of Assessments (SoA), CRF, SDTM etc.
1. You can create additional visits with different visit types that refer to each other or directly to the global anchor visit. In below example, visit 2 is used as time-baseline and named to be randomization visit
1. You can mark a visit as a SoA milestone, then the visit type will be defined as a SoA milestone and can be displayed in the SoA based on display option
1. Above the visit table, you can open a drawing of the study timeline view by using the arrow (see figure 3)
1. Below the timeline you can choose to have the timeline presented in days or weeks
1. If you place your mouse over the visit circles, you will get a tool tip showing the visit number, contact mode, visit type and timing in days and weeks

![Example - Showing timeline, tooltip for visit, preferred time unit](~@source/images/user_guides/guide_visits_03.png)

Figure 3: Example - Showing timeline, tooltip for visit, preferred time unit


**Visit stretching across more than one day (consecutive visit days in a visit)**

You can also create a visit 'group' when one single visit expands across several days. For this you use the functionality 'Anchor visit in visit group'. The anchor visit in the visit group can be any visit within the group as you can assign the rest of the visit days before or after the anchor visit.

You find this functionality in the add visit form, where you choose 'scheduled visit', then the relevant epoch and then 'Anchor visit in visit group'. Fill in the needed information.

![Visit Groups](~@source/images/user_guides/guide_visits_04.png)

Figure 4: Visit Groups

For adding additional visits to the visit group, you again choose 'scheduled visit', the relevant epoch and then 'Additional sub-visit'. This option only appears once an anchor visit in visit group has been created.

![Additional visits for a group](~@source/images/user_guides/guide_visits_05.png)

Figure 5: Additional visits for a group
 
When adding the additional sub-visit, you only get the choice to refer to the anchor visit(s) in visit group(s).

In the visit table, all visit days belonging to this visit lasting several days will appear with the same visit number. The difference can be seen in visit short name and timing. This functionality will usually be used when a single visit is stretching across several days and the visit days are not to be considered as separate visits, e.g., for a profile sampling that spans across days.
 
![Example - Visits in a visit group](~@source/images/user_guides/guide_visits_06.png)

Figure 6: Example - Visits in a visit group


## How to create Visit 0

The visit 0 is occasionally utilized in early phase studies. This visit is not expected to hold any assessments as Informed Consent is collected at a later visit, usually visit 1. Visit 0 is intended as an information visit, e.g. to inform subjects to attend visit 1 fasting.
> *Note:* Visit 0 must be an information visit, but information visit can be scheduled at any time in the study.

![visit_0](~@source/images/user_guides/Visit_0_1.png)
Figure 7: Visits 0 in a study

Follow the below steps to create an Information visit 0 in StudyBuilder:
1.	In studies/define study/study Structure/study visits: click on ”Add content” button
1.	In Visit scheduling type, select Scheduled visit and click Continue
1.	Select the screening or first study period (Epoch) and click continue
1.	Fill in the visit details by first selecting *Visit type=Information*
1.	Pick Contact mode as needed
1.	Mark visit as a SoA milestone per need (optional)
1.	Set time reference as Global Anchor visit
1.	Select time unit as needed
1.	Set timing as *negative* towards the global anchor visit, e.g. ’-28’ (days). *Note* that the timing must be before any existing Visit 1.
1.	Set visit window as needed (optional)
1.	StudyBuilder will now name this very first Information visit as Visit 0 (see green boxes in Figure 8)

![visit_0](~@source/images/user_guides/Visit_0_2.png)
Figure 8: Settings to create visit 0

## Repeating visits

A repeating visit is when a visit is repeated a number of times depending on how many times the subject visits their own physician based on the subject's need. When the subject comes to the physician, the same assessments (activities) are performed again. Repeating visits are often used in longitudinal and observational studies, where a patient or participant is followed over time to track changes in their health or behavior.

The frequency of the repeating visits can optionally be specified as repeated: daily, weekly or monthly. This refer to the delta between two repetition. If the visit repetition requires a different frequency than what is available on the pull-down list, then keep this item blank and enter specific repetition details into the "Visit Description" field. If the frequency is specified to be different in different periods of the study design then this should be specified as two sets of repeated visits.

The repeating visits is scheduled to start at a specific point in time and will be allocated a visit number in the schedule related to the starting point. In the Schedule of Activity the display of a repeated visit will e.g. for a visit 3 be like: V3.N - where the '.N' extension indicate this will be repeated a number of times.

> *Note:* It is important to differentiate between repeating visits and consecutive visits.
> For Repeating visits, you do not know in advance the number of repeats that will occur. If a fixed number of similar visits is planned then these should be created as single scheduled visits and be grouped in a consecutive visit group. They will then also display as one column in the protocol SoA, but each visit is still defined as a specific scheduled visit with timing and numbers.

1. Select to add a scheduled visit, select the related epoch, then select repeating visit as the visit subclass.
1. The option to also specify the repeating frequency will apear
1. The visit name and short name will include the '.n' extension to indicate this is a repeating visits.

![Repeating visits](~@source/images/user_guides/guide_visits_10.png)


## Adding a Non-Visit

From the add visit menu you can add a non-visit, that can be used as a technical placeholder for data collected outside the planned visit schedule


## Adding an Unscheduled Visit

From the add visit menu, you can add an unscheduled visit type. This is supposed to be a technical placeholder for data collected at an unscheduled visit, like Adverse events, additional sampling etc.


## Adding a Special Visit

The special visit is supposed to be used for early discontinuation of study treatment but has been made generic so it can be used for other purposes. 
The special visit is referencing to another existing visit. Example: Visit 10 is the planned End of treatment visit with a specific data collection (assigned activities). As always, subjects are allowed to skip treatment earlier and, in that case, an end of treatment data collection is needed. The special visit will in this case be visible as 10A.

![Example - Visit 10 and visit 10A](~@source/images/user_guides/guide_visits_07.png)

Figure 9: Example -  Visit 10 and visit 10A


## Adding a Manually defined visit

A manually defined visit is a type of visit for which the user must fully manually define the Visit name, Visit short name, Visit number and Unique visit number. 

When creating a visit, it is important to note that none of these items can be duplicated with values that already exist. Moreover, timing of such visit should not overlap with other entered visits. It is essential to ensure that newly created manually defined visit is placed in correct chronological order and that the defined visit names and numbers of this visit are reflecting that. 

Manually defined visits can be utilized, for instance, due to a protocol amendment, to add a new visit after the first patient has been enrolled in the study (FPFV) and data collection has already begun. In situation like this, addition of Scheduled visit type would cause a visit reordering and consequently changing their names, which may have serious consequences on data that were already collected. 

The manually defined visit enables the addition of a visit with timing and a name defined manually by the user, thus not impacting the order and names of visits that were initially set up.

![Example - Manually defined visit 2.1](~@source/images/user_guides/guide_visits_09.png)
Figure 10: Example -  Manually defined visit 2.1


## Visit Table Specific Functionalities

**Duplicate visit:** In the row actions it is possible to duplicate a visit if several visits are having the same attributes except for the timing. 

**Edit in table view:** The edit in table view puts most of the visit table into edit mode, so it possible to change most of the attributes. When you change e.g. the contact mode, you need to save the change. Once you have saved your changes you can close the edit mode in top of the table.
 
![Example - Edit in table view including saving on row level and Close edit mode](~@source/images/user_guides/guide_visits_08.png)
Figure 11: Example -  Edit in table view including saving on row level and Close edit mode


## The Visit Table

In the visit table, you get an overview of the visits added and their timing towards the reference visits (timepoints). Several timing columns are available to support different needs.

Column | Description
-- | --
Epoch | The epoch, the visit is assigned to
Visit Type | Based on the visit type codelist in the library. Example: Screening
SoA Milestone | Indicate the visit type is to be displayed as a SoA milestone
Visit Class | Scheduled visit, Unscheduled visit, Non-visit, Special Visit, Manually defined visit
Visit Subclass | Single visit, Anchor visit in visit grouo, Additional sub-visit, Repeating visit
Repeating frequency | For repeating visits the optional specification of the repeating frequency
Visit name | Visit as name. Example: Visit 2. Defined manually for Manually defined visits
Anchor visit in visit group | Indicator when visit is the anchor visit in a visit stretching across several days
Visit group | The visit group where this visit is used as anchor visit for other vsits in same group
Global anchor visit | Indicator if visit is global anchor visit (global reference) in the study
Contact mode | CDISC Visit contact mode codelist
Time Reference | Reference to typical global anchor visit or anchor visit in visit group
Timing | Timing towards time reference point
Visit number | Auto-numbered visit. Example: 2. Defined manually for Manually defined visits
Unique visit number | 3-digit visit number. Example: 200. Defined manually for Manually defined visits
Visit short name | Visit short name. Example: V2. Defined manually for Manually defined visits
Study duration days | Timing shown as days including label calculated as global anchor visit being day 0
Study duration weeks | Timing shown as weeks including label calculated as Global Anchor visit being in week 0
Visit window | The window for when the visit must take place relative to timing of visit. Example: -1/1
Collapsible visit group | If the visit is collapsed with other visits in the flowchart, the collapsed group is visual here
Show visit | Should visit be shown in the flowchart or not. Unscheduled visit and non-visit are par default not shown.
Visit description | Textual description of the visit, e.g., specific purpose
Epoch allocation rule | The rule used to calculate the epoch from, e.g. epoch starting from current visit or from the day after the previous visit
Visit start rule  | Start rule
Visit end rule | End rule
Study day | Timing relative to the reference timing in days. Example: Day 1
Study week | Timing relative to the reference timing in weeks. Example: Week 1
Week in Study | Same as Study duration weeks, but written as 'Week x', can be used as template parameter in study endpoint time frames
Modified | Date
Modified by | Username of user that made the last change



