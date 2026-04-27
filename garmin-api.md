GARMIN INTERNATIONALGARMIN INTERNATIONAL

### Garmin Connect DeveloperGarmin Connect Developer

### ProgramProgram

## Training APITraining API

##### Version 1.0.0Version 1.0.

#### CONFIDENTIALCONFIDENTIAL

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
22
Garmin InternationalGarmin International
```
Table of ContentsTable of Contents

1.1. Revision History ..................................Revision History .............................................................................................................................................................................................................................................. 3 3

2. Getting Started ................................2. Getting Started ................................................................................................................................................................................................................................................ 4.... 4
    2.1.2.1. Purpose Purpose of of the the API API ............ ............................................................................................................................................................................................................................................................................. 4... 4
    2.2.2.2. Consumer Consumer Key Key and and Secret Secret ................................................................................................................................................................................................................................................................. 4..... 4
    2.3.2.3. User User Registration Registration ............................................................................................................................................................................................................................................................................................. ..... 55

```
2.4.2.4. Training API ImportTraining API ImportTypesTypes............................................................................................................................................................................................................................................................... ..... 55
2.5.2.5. Requesting Requesting a a Production Production Key Key ............. .............................................................................................................................................................................................................................................. 5. 5
2.6.2.6. API API Rate Rate Limiting Limiting or or Excessive Excessive Usage ......................Usage ....................................................................................................................................................................................................... ....... 66 
```
3. Training API Endpoint Details ..................3. Training API Endpoint Details ....................................................................................................................................................................... 7............................................... 7
    3.1. 3.1. Training Training API API Permissions Permissions .................................................................................................................................................................................................................................................................. 7........ 7
    3.2.3.2. Workouts Workouts ....................................................................................................................................................................................................................................................................................................................... ... 88
       3.2.1.3.2.1. Field Field Definitions Definitions ......................................................................................................................................................................................................................................................................................................... ................... 88
       3.2.2.3.2.2. Example Example JSON JSON ............................................................................................................................................................................................................................................................................................................. ................. 1111
       3.2.3.3.2.3. Create...........................Create............................................................................................................................................................................................................................................................................................................................ 1212.
       3.2.4.3.2.4. Retrieve Retrieve ....................................................................................................................................................................................................................................................................................................................... ........................... 1313
       3.2.5.3.2.5. Update Update ......................................................................................................................................................................................................................................................................................................................... ........................... 1313
       3.2.6. 3.2.6. Delete Delete ....................................................................................................................................................................................................................................................................................................................................................... 1414 .
3.3. 3.3. Workout Workout Schedules Schedules ......................................................................................................................................................................................................................................................................... 14............. 14

```
3.3.1.3.3.1. Field Field Definitions Definitions ....................................................................................................................................................................................................................................................................................................... ................. 1414
3.3.2.3.3.2. Example Example JSON JSON ............................................................................................................................................................................................................................................................................................................. ................. 1414
3.3.3.3.3.3. Create...........................Create............................................................................................................................................................................................................................................................................................................................ 1515.
3.3.4.3.3.4. Retrieve Retrieve ....................................................................................................................................................................................................................................................................................................................... ........................... 1515
3.3.5.3.3.5. Update Update ......................................................................................................................................................................................................................................................................................................................... ........................... 1515
3.3.6. 3.3.6. Delete Delete ....................................................................................................................................................................................................................................................................................................................................................... 1616.
3.3.7.3.3.7. Retrieve Retrieve by by Date Date .......................................................................................................................................................................................................................................................................................................... 16. 16...........
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
33
Garmin InternationalGarmin International
```
###### 1.1. Revision HistoryRevision History

```
Version Version Date Date RevisionsRevisions
```
1.0 1.0 12/01/2020 12/01/2020 Initial Initial revisionrevision

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
44
Garmin InternationalGarmin International
```
2. Getting Started2. Getting Started

2.1.2.1. Purpose of the APIPurpose of the API

```
The Garmin Connect Training API is the The Garmin Connect Training API is the underlying munderlying mechanism by which users can opt to impoechanism by which users can opt to importrt
workouts and workout schedules, regardless of activworkouts and workout schedules, regardless of activity type ity type from third-party platforms into theirfrom third-party platforms into their
Garmin Connect account, making it eGarmin Connect account, making it easy to manage thasy to manage this type of information in a centralis type of information in a centralized ized location.location.
```
2.2.2.2. Consumer Key and SecretConsumer Key and Secret

```
Garmin Connect Training API partners will be Garmin Connect Training API partners will be providprovided with a consumer key and secret used to gaied with a consumer key and secret used to gainn
access to the Training API. The access to the Training API. The consumer key is useconsumer key is used to uniquely identify a partnerd to uniquely identify a partner and and the consumerthe consumer
secret is used to validate that the requests receivsecret is used to validate that the requests received are from that partner and not a third-party thated are from that partner and not a third-party that has has
gained unauthorized access to the consumer key. gained unauthorized access to the consumer key. TheThe consumer key can be considered public consumer key can be considered public
information, but the consumer secret is private. information, but the consumer secret is private. FoFor the security of users, the consumer secret shour the security of users, the consumer secret should beld be
secured and never sent over a network in plain textsecured and never sent over a network in plain text. It is not permitted to embed the consumer secret. It is not permitted to embed the consumer secret
into consumer products like mobile apps.into consumer products like mobile apps.
```
```
Consumer key credentials are createConsumer key credentials are created using the Deved using the Developer Portal and creating Appsloper Portal and creating Apps
(https://developerportal.garmin.com/user/me/apps?pr(https://developerportal.garmin.com/user/me/apps?program=829ogram=829).). Each app represents a uniqueEach app represents a unique
consumer key. Your first app will generate consumer key. Your first app will generate an evaluan evaluation-level consumer key that is rate limitation-level consumer key that is rate limited.ed.
Once your integration has been verified for Once your integration has been verified for productproduction, subsequent apps will create consumer keion, subsequent apps will create consumer keysys
with production-with production-level access. Please see “Requesting a Production Klevel access. Please see “Requesting a Production Key”ey”below for more information.below for more information.
```
```
Note:Note:
Multiple consumer keys should be created to corrMultiple consumer keys should be created to correspespond to projects or implementations whose userond to projects or implementations whose user
base is logically separated. A common scenario is fbase is logically separated. A common scenario is for one or one partner to manage user data partner to manage user data from multiplefrom multiple
other companies. other companies. A new key should be created and asA new key should be created and associated with eacsociated with each managed company so thath managed company so that
Garmin users can make an informed decGarmin users can make an informed decision to conseision to consent to sharing their data with just thnt to sharing their data with just that at company. company.
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
55
Garmin InternationalGarmin International
```
2.3.2.3. User RegistrationUser Registration

```
Before a partner can write data to a user’s accountBefore a partner can write data to a user’s account, the u, the user must grant the partner write access.ser must grant the partner write access.
Please refer to the Please refer to the detailed Garmin OAuth documentadetailed Garmin OAuth documentation for details on tion for details on acquiring, authorizing, andacquiring, authorizing, and
signing with a User Access Token signing with a User Access Token (UAT) to write dat(UAT) to write data to a Garmin user’s account.a to a Garmin user’s account.
```
2.4.2.4. Training API Import TypesTraining API Import Types

```
All data uploaded to Garmin Connect via the TraininAll data uploaded to Garmin Connect via the Training API cg API can either be categorized as an either be categorized as a workout or aa workout or a
workout schedule. workout schedule. The API allows for the The API allows for the standard CRUD operations on standard CRUD operations on these two data types.these two data types.
```
```
•• Workout Workout 
A workout contains a list of steps for A workout contains a list of steps for the user to the user to take as part of their workout, as well take as part of their workout, as well asas
metadata about the workout (e.g. description, sportmetadata about the workout (e.g. description, sport type, etc type, etc.)..).
```
```
•• Workout ScheduleWorkout Schedule
A workout schedule allows a previously defined workA workout schedule allows a previously defined workout to be out to be scheduled for ascheduled for a
specified day.specified day.
```
2.5.2.5. Requesting a Production KeyRequesting a Production Key

```
The first consumer key generated through theThe first consumer key generated through the  DevelDeveloper Portaloper Portal is is an evaluation key. This key is rate  an evaluation key. This key is rate
limited and should only be used for testing, evalulimited and should only be used for testing, evaluaation, and development. To receive productiontion, and development. To receive production
level credentials, Garmin must review and approve tlevel credentials, Garmin must review and approve the he Training API integration to ensure a hig Training API integration to ensure a high-h-
quality user experience in Garmin quality user experience in Garmin Connect. Connect. Garmin also reserves the right to Garmin also reserves the right to review partnerreview partner
applications and/or websites to ensure proper usageapplications and/or websites to ensure proper usage of Garmin assets (e of Garmin assets (e.g. device images) and.g. device images) and
adherence to Garmin brand guidelines.adherence to Garmin brand guidelines.
```
```
Please email Training API support at connect-supporPlease email Training API support at connect-support@developer.garmin.com to request andt@developer.garmin.com to request and
schedule a production readiness review. Garmin willschedule a production readiness review. Garmin will review the review the following technical aspects of thefollowing technical aspects of the
integration:integration:
```
```
•• Authorization and correct use of UATs for at Authorization and correct use of UATs for at least least two Garmin Connect users;two Garmin Connect users;
•• No unnecessary or excessive API call utilization orNo unnecessary or excessive API call utilization or volume;volume;
•• Proper handling of quota violations and subsequent Proper handling of quota violations and subsequent retry attempts.retry attempts.
```
```
If the technical integration is not approved, any oIf the technical integration is not approved, any open issues must be corrected, and another pen issues must be corrected, and another reviewreview
will be required. Once the technical will be required. Once the technical integration isintegration is approved, Garmin may conduct a user approved, Garmin may conduct a user experexperienceience
review. This review can be achieved by review. This review can be achieved by application application demonstration to Garmin via video confedemonstration to Garmin via video conference orrence or
other mutually agreed upon method. This review is uother mutually agreed upon method. This review is used to sed to confirm the following criteria are metconfirm the following criteria are met::
```
```
•• Proper representation of all Garmin trademarked/copProper representation of all Garmin trademarked/copyrighted terms;yrighted terms;
•• Proper representation Garmin products and product iProper representation Garmin products and product images; andmages; and
•• User experience (UX) flow does User experience (UX) flow does not misrepresent Garnot misrepresent Garmin or reflect Garmin poorly.min or reflect Garmin poorly.
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
66
Garmin InternationalGarmin International
```
```
Once all reviews are approved, production creOnce all reviews are approved, production credentiadentials (consumer key and secret) may be requestedls (consumer key and secret) may be requested
via the Garmin Connect Developer Portal.via the Garmin Connect Developer Portal.
```
2.6.2.6.  API Rate Limiting or Excessive Usage API Rate Limiting or Excessive Usage

To manage capacity and ensure system stability, GarTo manage capacity and ensure system stability, Garmin Training API implementations may bemin Training API implementations may be

```
subject to rate limiting. subject to rate limiting. If any of the following lIf any of the following limits are problematic for imits are problematic for your implementation,your implementation,
please contact connectplease contact connect-support@developer.garmin.-support@developer.garmin.com to com to discuss alternatives.discuss alternatives.
```
Please plan the implementation with the following lPlease plan the implementation with the following limitations in mind:imitations in mind:

Evaluation Rate LimitsEvaluation Rate Limits

```
•• 100 API call requests per 100 API call requests per partner per minute - a partner per minute - a rolling 60 second window sumrolling 60 second window summing the Oauthming the Oauth
requests and API calls.requests and API calls.
•• 200 API call requests per user per day -200 API call requests per user per day -a rolling 24‐hour window excluding Oauth requests.a rolling 24‐hour window excluding Oauth requests.
```
Production Rate limitsProduction Rate limits^

```
•• 6000 API call requests 6000 API call requests per partner per minute - per partner per minute - a rolling 60 second windowa rolling 60 second window summing the summing the
Oauth requests and API calls.Oauth requests and API calls.
•• 6000 API call requests per user per day - a rolling6000 API call requests per user per day - a rolling24‐hour window excluding Oauth requests.24‐hour window excluding Oauth requests.
```
```
If one or both of tIf one or both of the above limits are exceeded by he above limits are exceeded by a partner or a speca partner or a specific user, the subsequent APIific user, the subsequent API
call request attempts will receive an HTTP Status Ccall request attempts will receive an HTTP Status Code 429 (too many requests). ode 429 (too many requests). The call or calls inThe call or calls in
question will need to be attempted again later.question will need to be attempted again later.
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
77
Garmin InternationalGarmin International
```
3. Training API Endpoint Details3. Training API Endpoint Details

3.1. Training API Permissions3.1. Training API Permissions

```
Consumer can have multiple permissions like “ActiviConsumer can have multiple permissions like “Activity Export”ty Export” and and“Workout Import”“Workout Import” set up with GC. set up with GC.
User User while while signing signing up up may may only only opt opt in in for for fewer fewer permissions, permissions, so so this this endpoint endpoint helps helps in in fetching fetching thethe
```
permissions for that particular user.permissions for that particular user.

Example response for this endpoint:Example response for this endpoint:

```
{[{[
"WORKOUT_IMPORT""WORKOUT_IMPORT"
]}]}
```
```
Method & Method & URL: URL: GETGET https://apis.garmin.com/userPermissions/https://apis.garmin.com/userPermissions/
Response body: The retrieved user permissions in JSResponse body: The retrieved user permissions in JSON.ON.
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 User User Permissions Permissions retrievedretrieved

401 401 UnauthorizedUnauthorized

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

The below section provides details for both theThe below section provides details for both theWorkoutWorkoutandandWorkout ScheduleWorkout Scheduleendpoints.endpoints.

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
88
Garmin InternationalGarmin International
```
3.2.3.2. WorkoutsWorkouts

3.2.1.3.2.1. Field DefinitionsField Definitions

WorkoutWorkout (^) DataData Type Type DescriptionDescription
workoutId workoutId Long Long A A unique unique identifier identifier for for the the Workout. Workout. This This field field is is not not necessary necessary for for Create Create
action and will be set automatically.action and will be set automatically.
ownerId ownerId Long Long A A unique unique identifier identifier for for the the owner owner of of the the Workout. Workout. This This field field is is notnot
necessary for Create workouts, but necessary for necessary for Create workouts, but necessary for upupdate.date.
workoutName workoutName String String The The name name of of the the Workout. Workout.
description description String String A A description description of of the the Workout Workout with with a a maximum maximum length length of of 1024 1024
characters. Longer descriptions will be truncated.characters. Longer descriptions will be truncated.
updatedDate updatedDate String String A A datetime datetime representing representing the the last last update update time time of of the the Workout, Workout, formattedformatted
as YYYY-mm-dd. Example: "2019-01-as YYYY-mm-dd. Example: "2019-01-14T16:25:10.0”. This field is not14T16:25:10.0”. This field is not
necessary for Create or Update actions and necessary for Create or Update actions and will be will be set automatically.set automatically.
createdDate createdDate String String A A datetime datetime representing representing the the creation creation time time of of the the Workout, Workout, formatted formatted asas
YYYY-mm-dd. Example: "2019-01-YYYY-mm-dd. Example: "2019-01-14T16:25:10.0”. This field is not14T16:25:10.0”. This field is not
necessary for Create or Update actions and necessary for Create or Update actions and will be will be set automatically.set automatically.
sport sport String String The The type type of of sport. sport. Valid Valid values: values: RUNNING, RUNNING, CYCLING, CYCLING, LAP_SWIMMING,LAP_SWIMMING,
STRENGTH_TRAINING, CARDIO_TRAINING, GENERIC (supporSTRENGTH_TRAINING, CARDIO_TRAINING, GENERIC (supported byted by
limited devices) , YOGA, PILATESlimited devices) , YOGA, PILATES
estimatedDurationInSecs estimatedDurationInSecs Integer Integer The The estimated estimated duration duration of of the the Workout Workout in in seconds. seconds. This This value value isis
calculated server-side and will be ignored in Creatcalculated server-side and will be ignored in Create and e and Update actions.Update actions.
estimatedDistanceInMeters estimatedDistanceInMeters Double Double The The estimated estimated distance distance of of the the Workout Workout in in meters. meters. This This value value isis
calculated server-side and will be ignored in Creatcalculated server-side and will be ignored in Create and e and Update actions.Update actions.
poolLength poolLength Double Double The The length length of of the the pool. pool. Used Used only only when when sport sport = = LAP_SWIMMING.LAP_SWIMMING.
poolLengthUnit poolLengthUnit String String The The unit unit of of the the pool pool length. length. Valid Valid values: values: YARD, YARD, METER. METER. Used Used only only ifif
poolLength is set.poolLength is set.
workoutProvider workoutProvider String String The The workout workout provider provider to to display display to to the the user. user.
workoutSourceId workoutSourceId String String The The workout workout provider provider to to use use for for internal internal tracking tracking purposes. purposes. This This valuevalue
should be the same as workoutProvider unless otherwshould be the same as workoutProvider unless otherwise noted.ise noted.
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content
measurement, audience research, and services development, personalised advertising, and personalised content.
Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.
Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this
personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie
icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
Privacy Policy
Third Parties
Customize Your Choices
Accept All


```
99
Garmin InternationalGarmin International
```
steps steps List<Step> List<Step> A A list list of of Steps Steps that that specify specify the the details details of of the the workout. workout.

WorkoutStep WorkoutStep Data Data Type Type DescriptionDescription

```
type type String String The The type type of of Step. Step. Valid Valid values values are are WorkoutStep WorkoutStep andand
WorkoutRepeatStep. WorkoutStep type Steps contains WorkoutRepeatStep. WorkoutStep type Steps contains details of thedetails of the
Step itself, while workoutRepeatSteps contain a subStep itself, while workoutRepeatSteps contain a sub-list of -list of Steps thatSteps that
should be repeated until a condition is met as should be repeated until a condition is met as specspecified in theified in the
repeatType and repeatValue field.repeatType and repeatValue field.
```
```
stepId stepId Long Long A A unique unique ID ID is is generated generated for for the the Step. Step. This This value value is is calculated calculated server-server-
side and will be ignored in Create actions.side and will be ignored in Create actions.
```
stepOrder stepOrder Integer Integer Represents Represents the the order order of of the the Step. Step.

```
repeatType repeatType StringString The type of the repeat action, specifying hoThe type of the repeat action, specifying how long w long or until when theor until when the
user should repeat the sub-list of Steps. Used onlyuser should repeat the sub-list of Steps. Used only forfor
WorkoutRepeatSteps. Valid values: REPEAT_UNTIL_STEPWorkoutRepeatSteps. Valid values: REPEAT_UNTIL_STEPS_CMPLT,S_CMPLT,
REPEAT_UNTIL_TIME, REPEAT_UNTIL_DISTANCE,REPEAT_UNTIL_TIME, REPEAT_UNTIL_DISTANCE,
REPEAT_UNTIL_CALORIES, REPEAT_UNTIL_HR_LESS_THAN,REPEAT_UNTIL_CALORIES, REPEAT_UNTIL_HR_LESS_THAN,
REPEAT_UNTIL_HR_GREATER_THAN,REPEAT_UNTIL_HR_GREATER_THAN,
REPEAT_UNTIL_POWER_LESS_THAN,REPEAT_UNTIL_POWER_LESS_THAN,
REPEAT_UNTIL_POWER_GREATER_THAN,REPEAT_UNTIL_POWER_GREATER_THAN,
REPEAT_UNTIL_POWER_LAST_LAP_LESS_THAN,REPEAT_UNTIL_POWER_LAST_LAP_LESS_THAN,
REPEAT_UNTIL_MAX_POWER_LAST_LAP_LESS_THANREPEAT_UNTIL_MAX_POWER_LAST_LAP_LESS_THAN
```
```
repeatValue repeatValue Double Double The The value value of of the the repeat repeat action. action. When When paired paired with with repeatType, repeatType, specifiesspecifies
how long or until when the user should repeat the show long or until when the user should repeat the sublist of ublist of steps. Usedsteps. Used
only for WorkoutRepeatSteps.only for WorkoutRepeatSteps.
```
steps steps List<Step> List<Step> The The list list of of steps steps that that should should be be repeated repeated as as specified specified by by repeatType repeatType andand

repeatValue. Used only for repeatValue. Used only for WorkoutRepeatSteps.WorkoutRepeatSteps.

```
intensity intensity String String The The intensity intensity of of the the Step. Step. Valid Valid values: values: REST, REST, WARMUP, WARMUP, COOLDOWN,COOLDOWN,
RECOVERY, INTERVALRECOVERY, INTERVAL
```
```
description description String String A A description description of of the the Step Step with with a a maximum maximum of of 512 512 characters. characters. LongerLonger
descriptions will be truncated.descriptions will be truncated.
```
```
durationType durationType String String The The type type of of duration. duration. Paired Paired with with durationValue, durationValue, this this represents represents thethe
relative duration of the Step. Valid values: TIME, relative duration of the Step. Valid values: TIME, DISTANCE,DISTANCE,
HR_LESS_THAN, HR_GREATER_THAN, CALORIES, OPEN,HR_LESS_THAN, HR_GREATER_THAN, CALORIES, OPEN,
POWER_LESS_THAN, POWER_GREATER_THAN, REPETITION_TIMPOWER_LESS_THAN, POWER_GREATER_THAN, REPETITION_TIME,E,
REPS, TIME_AT_VALID_CDA, FIXED_RESTREPS, TIME_AT_VALID_CDA, FIXED_REST
```
durationValue durationValue Double Double The The duration duration value. value. Pair Pair with with durationType, durationType, this this represents represents the the relative relative

duration of the Step.duration of the Step.

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1010
Garmin InternationalGarmin International
```
```
durationValueType durationValueType String String A A modifier modifier for for duration duration value value used used only only for for HR HR and and POWER POWER types types toto
express units. Valid values: PERCENT, MILE, KILOMETexpress units. Valid values: PERCENT, MILE, KILOMETER, METER, YARDER, METER, YARD
```
```
targetType targetType String String The The type type of of target target for for this this Step. Step. Valid Valid values: values: SPEED, SPEED, HEART_RATE,HEART_RATE,
OPEN, CADENCE, POWER, GRADE, RESISTANCE, POWER_3S,OPEN, CADENCE, POWER, GRADE, RESISTANCE, POWER_3S,
POWER_10S, POWER_30S, POWER_LAP, SWIM_STROKE, SPEEDPOWER_10S, POWER_30S, POWER_LAP, SWIM_STROKE, SPEED_LAP,_LAP,
```
HEART_RATE_LAP, PACE (as speed in m/s)HEART_RATE_LAP, PACE (as speed in m/s)

```
targetValue targetValue Double Double The The target target HR HR or or power power zone zone to to be be used used for for this this Step. Step. Target Target zones zones mustmust
have been previously defined and saved.have been previously defined and saved.
```
```
targetValueLow targetValueLow Double Double The The lowest lowest value value for for the the target target range. range. Used Used to to specify specify a a custom custom rangerange
instead of specifying a target zone through targetVinstead of specifying a target zone through targetValue.alue.
```
```
targetValueHigh targetValueHigh Double Double The The highest highest value value for for the the target target range. range. Used Used to to specify specify a a custom custom rangerange
instead of specifying a target zoinstead of specifying a target zone through targetVne through targetValue.alue.
```
```
targetValueType targetValueType String String A A modifier modifier for for target target value value used used only only for for HR HR and and POWER POWER types types toto
express units. Valid values: PERCENT, MILE, KILOMETexpress units. Valid values: PERCENT, MILE, KILOMETER, METER, YARDER, METER, YARD
```
```
strokeType strokeType String String The The type type of of stroke stroke for for this this Step. Step. Used Used only only in in LAP_SWIMMINGLAP_SWIMMING
Workouts. Valid values: BACKSTROKE, BREASTSTROKE, DRWorkouts. Valid values: BACKSTROKE, BREASTSTROKE, DRILL,ILL,
BUTTERFLY, FREESTYLE, MIXED, IMBUTTERFLY, FREESTYLE, MIXED, IM
```
```
equipmentType equipmentType StringString
The type of equipment needed for this Step. CurrentThe type of equipment needed for this Step. Currently used only ly used only forfor
LAP_SWIMMING Workouts. Valid values: NONE, SWIM_FINLAP_SWIMMING Workouts. Valid values: NONE, SWIM_FINS,S,
SWIM_KICKBOARD, SWIM_PADDLES, SWIM_PULL_BUOY,SWIM_KICKBOARD, SWIM_PADDLES, SWIM_PULL_BUOY,
SWIM_SNORKELSWIM_SNORKEL
```
```
exerciseCategory exerciseCategory String String The The exercise exercise category category for for this this Step. Step. Used Used only only for for STRENGTH_TRAINING STRENGTH_TRAINING
and CARDIO_TRAINING Workouts. Valid values: BENCH_Pand CARDIO_TRAINING Workouts. Valid values: BENCH_PRESS,RESS,
CALF_RAISE, CARDIO, CARRY, CHOP, CORE, CRUNCH, CURLCALF_RAISE, CARDIO, CARRY, CHOP, CORE, CRUNCH, CURL , DEADLIFT, , DEADLIFT,
FLYE, HIP_RAISE, HIP_STABILITY, HIP_SWING, HYPEREXTEFLYE, HIP_RAISE, HIP_STABILITY, HIP_SWING, HYPEREXTENSION,NSION,
```
```
LATERAL_RAISE, LEG_CURL, LEG_RAISE, LUNGE, OLYMPIC_LATERAL_RAISE, LEG_CURL, LEG_RAISE, LUNGE, OLYMPIC_LIFT, PLANK,LIFT, PLANK,
PLYO, PULL_UP, PUSH_UP, ROW, SHOULDER_PRESS,PLYO, PULL_UP, PUSH_UP, ROW, SHOULDER_PRESS,
SHOULDER_STABILITY, SHRUG, SIT_UP, SQUAT, TOTAL_BODYSHOULDER_STABILITY, SHRUG, SIT_UP, SQUAT, TOTAL_BODY , ,
TRICEPS_EXTENSION, WARM_UP, RUN, BIKE, CARDIO_SENSORTRICEPS_EXTENSION, WARM_UP, RUN, BIKE, CARDIO_SENSORS,S,
UNKNOWN, INVALIDUNKNOWN, INVALID
```
```
exerciseName exerciseName String String The The exercise exercise name name for for this this Step. Step. Used Used only only for for STRENGTH_TRAINING STRENGTH_TRAINING
and CARDIO_TRAINING Workouts.and CARDIO_TRAINING Workouts.
```
```
weightValue weightValue Double Double The The weight weight value value for for this this Step Step in in kilograms. kilograms. Used Used only only forfor
STRENGTH_TRAINING Workouts.STRENGTH_TRAINING Workouts.
```
```
weightDisplayUnit weightDisplayUnit String String The The units units in in which which to to display display the the weightValue weightValue to to the the user, user, if if aa
weightValue exists. The display unit does not impacweightValue exists. The display unit does not impact weightValue withint weightValue within
the Training API, only for display. Valid values: Othe Training API, only for display. Valid values: OTHER, KILOGRAM,THER, KILOGRAM,
```
POUNDPOUND

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1111
Garmin InternationalGarmin International
```
3.2.2.3.2.2. Example JSONExample JSON

The following is an example of a WorThe following is an example of a Workout in JSON.kout in JSON.

```
{{
"workoutId": 2201,"workoutId": 2201,
"ownerId": 232,"ownerId": 232,
"workoutName": "Bike Workout","workoutName": "Bike Workout",
"description": null,"description": null,
"updatedDate": "updatedDate": "2018-10-23T21:17:"2018-10-23T21:17:53.0",53.0",
"createdDate": "createdDate": "2018-10-23T21:17:"2018-10-23T21:17:53.0",53.0",
"sport": "CYCLING","sport": "CYCLING",
"estimatedDurat"estimatedDurationInSecs": ionInSecs": null,null,
"estimatedDista"estimatedDistanceInMeters": nceInMeters": null,null,
"poolLength": null,"poolLength": null,
"poolLengthUnit"poolLengthUnit": ": null,null,
"workoutProvide"workoutProvider": r": null,null,
"workoutSourceI"workoutSourceId": d": null,null,
"steps": ["steps": [
```
```
{{
"type": "WorkoutStep","type": "WorkoutStep",
"stepId": 1475,"stepId": 1475,
"stepOrder": 1,"stepOrder": 1,
"intensity": "WARMUP","intensity": "WARMUP",
"description": null,"description": null,
"durationType": "CALORIES","durationType": "CALORIES",
"durationValue": 2,"durationValue": 2,
"durationValueTy"durationValueType": pe": null,null,
"targetType": "OPEN","targetType": "OPEN",
"targetValue": null,"targetValue": null,
"targetValueLow""targetValueLow": : null,null,
"targetValueHigh"targetValueHigh": ": null,null,
"targetValueType"targetValueType": ": null,null,
"strokeType": null,"strokeType": null,
"equipmentType": null,"equipmentType": null,
"exerciseCategor"exerciseCategory": y": null,null,
"exerciseName": null,"exerciseName": null,
"weightValue": null,"weightValue": null,
"weightDisplayUn"weightDisplayUnit": it": nullnull
},},
{{
"type": "type": "WorkoutRepeatSt"WorkoutRepeatStep",ep",
"stepId": 1476,"stepId": 1476,
"stepOrder": 2,"stepOrder": 2,
"repeatType": null,"repeatType": null,
"repeatValue": null,"repeatValue": null,
```
```
"steps": ["steps": [
{{
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1212
Garmin InternationalGarmin International
```
```
"type": "WorkoutStep","type": "WorkoutStep",
"stepId": 1477,"stepId": 1477,
"stepOrder": 5,"stepOrder": 5,
"intensity": "ACTIVE","intensity": "ACTIVE",
"description": null,"description": null,
"durationType": "TIME","durationType": "TIME",
"durationValue": 120,"durationValue": 120,
```
"durationValueTyp"durationValueTyp"targetType": "POWER","targetType": "POWER",e": e": null,null,

```
"targetValue": 1,"targetValue": 1,
"targetValueLow"targetValueLow": ": null,null,
"targetValueHigh""targetValueHigh": : null,null,
"targetValueType""targetValueType": : null,null,
"strokeType": null,"strokeType": null,
"equipmentType": null,"equipmentType": null,
"exerciseCategory"exerciseCategory": ": null,null,
"exerciseName": null,"exerciseName": null,
"weightValue": null,"weightValue": null,
"weightDisplayUni"weightDisplayUnit": t": nullnull
},},
{{
"type": "WorkoutStep","type": "WorkoutStep",
"stepId": 1478,"stepId": 1478,
"stepOrder": 6,"stepOrder": 6,
"intensity": "ACTIVE","intensity": "ACTIVE",
"description": null,"description": null,
"durationType": "DISTANCE","durationType": "DISTANCE",
"durationValue": 32186.880859,"durationValue": 32186.880859,
"durationValueTyp"durationValueType": e": "MILE","MILE",
"targetType": "OPEN","targetType": "OPEN",
"targetValue": null,"targetValue": null,
"targetValueLow": null,"targetValueLow": null,
"targetValueHigh""targetValueHigh": : null,null,
"targetValueType""targetValueType": : null,null,
```
"strokeType": null,"strokeType": null,"equipmentType": null,"equipmentType": null,

```
"exerciseCategory"exerciseCategory": ": null,null,
"exerciseName": null,"exerciseName": null,
"weightValue": null,"weightValue": null,
"weightDisplayUni"weightDisplayUnit": t": nullnull
}}
]]
}}
]]
}}
```
3.2.3.3.2.3. CreateCreate

This request is toThis request is tocreatecreate a workout by/for a user: a workout by/for a user:

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1313
Garmin InternationalGarmin International
```
```
Method & Method & URL: URL: POSTPOST https://apis.garmin.com/training-api/workout/https://apis.garmin.com/training-api/workout/
Request body: The new workout in JSON.Request body: The new workout in JSON.A workout ID should not be A workout ID should not be included.included.
Content-Type: application/jsonContent-Type: application/json
Response Body: The newly-created workout as JSON.Response Body: The newly-created workout as JSON.
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 Workout Workout successfully successfully createdcreated

401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User Permission Permission errorerror

429429 Quota violation / rate‐limitinQuota violation / rate‐limitingg

3.2.4.3.2.4. RetrieveRetrieve

This request is toThis request is toretrieveretrieve a workout by/for a user: a workout by/for a user:

```
Method & Method & URL: URL: GETGET https://apis.garmin.com/training-api/workout/{wohttps://apis.garmin.com/training-api/workout/{workorkoutId}utId}
Response body: The retrieved workout in JSON.Response body: The retrieved workout in JSON.
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 Workout Workout successfully successfully retrievedretrieved

401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

3.2.5.3.2.5. UpdateUpdate

```
This request is toThis request is toupdateupdate a workout by/for a user: a workout by/for a user:
Method Method & & URL: URL: PUTPUT https://apis.garmin.com/training-api/workout/{wohttps://apis.garmin.com/training-api/workout/{workorkoutId}utId}
Request body: The full updated workout in JSON.Request body: The full updated workout in JSON.
Content-Type: application/jsonContent-Type: application/json
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

204 204 Workout Workout successfully successfully updatedupdated

401401 User Access Token doesn’t existUser Access Token doesn’t exist

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1414
Garmin InternationalGarmin International
```
404 404 Not Not found found

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

3.2.6. Delete3.2.6. Delete

```
This request is toThis request is todeletedelete a workout by/for a user: a workout by/for a user:
Method & Method & URL: URL: DELETEDELETE https://apis.garmin.com/training-api/workout/https://apis.garmin.com/training-api/workout/{worko{workoutId}utId}
```
RResponse code: esponse code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 Workout Workout successfully successfully deleteddeleted

401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

3.3. Workout Schedules3.3. Workout Schedules

3.3.1.3.3.1. Field DefinitionsField Definitions

Field Field Name Name DescriptionDescription

scheduleId scheduleId A A unique unique identifier identifier for for the the workout workout scheduleschedule

workoutId workoutId The The ID ID of of the the workout workout to to which which the the schedules schedules refersrefers

datedate The scheduled date, formatted as ‘YYYYThe scheduled date, formatted as ‘YYYY-mm-dd-mm-dd

3.3.2.3.3.2. Example JSONExample JSON

```
{{
"scheduleId":123,"scheduleId":123,
"workoutId":123,"workoutId":123,
"date":"2019-01-31""date":"2019-01-31"
}}
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1515
Garmin InternationalGarmin International
```
3.3.3.3.3.3. CreateCreate

```
This request is toThis request is tocreatecreate a workout schedule by/for a user: a workout schedule by/for a user:
Method & Method & URL: URL: POSTPOST https://apis.garmin.com/training-api/schedule/https://apis.garmin.com/training-api/schedule/
Request body: A workout schedule to creatRequest body: A workout schedule to create.e.A schedule Id should not be A schedule Id should not be included.included.
Content-Type: application/jsonContent-Type: application/json
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 Workout Workout schedule schedule successfully successfully created/addedcreated/added

401 401 User User AccessAccessToken doesn’t existToken doesn’t exist

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

3.3.4.3.3.4. RetrieveRetrieve

```
This request is toThis request is toretrieveretrieve a workout schedule by/for a user: a workout schedule by/for a user:
Method & URL:Method & URL:
GETGET https://apis.garmin.com/training-api/schedule/{whttps://apis.garmin.com/training-api/schedule/{workorkoutScheduleId}outScheduleId}
Response body: The retrieved workout schedule.Response body: The retrieved workout schedule.
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 Workout Workout schedule schedule successfully successfully retrievedretrieved

401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User permission permission errorerror

429 429 Quota Quota violation violation //rate‐limitingrate‐limiting

3.3.5.3.3.5. UpdateUpdate

```
This request is toThis request is toupdateupdate a workout schedule by/for a user: a workout schedule by/for a user:
Method & URL:Method & URL:
PUTPUT https://apis.garmin.com/training-api/schedule/{whttps://apis.garmin.com/training-api/schedule/{workorkoutScheduleId}outScheduleId}
Request body: The full workout schedule in JSON.Request body: The full workout schedule in JSON.
Content-Type: application/jsonContent-Type: application/json
Response body: The updated workout schedule.Response body: The updated workout schedule.
```
We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All


```
1616
Garmin InternationalGarmin International
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

204 204 Workout Workout schedule schedule successfully successfully updatedupdated

401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

3.3.6. Delete3.3.6. Delete

```
This request is toThis request is todeletedelete a workout schedule by/for a user: a workout schedule by/for a user:
Method & URL:Method & URL:
DELETEDELETE https://apis.garmin.com/training-api/schedulehttps://apis.garmin.com/training-api/schedule/{work/{workoutScheduleId}outScheduleId}
```
Response code:Response code:

HTTP HTTP Response Response Status Status DescriptionDescription

200 200 Workout Workout schedule schedule successfully successfully deleteddeleted

401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

3.3.7.3.3.7. Retrieve by DateRetrieve by Date

```
This request is used toThis request is used toretrieveretrieve workout schedule by/for a user workout schedule by/for a userby date rangeby date range::
Method & URL: GETMethod & URL: GET https://apis.garmin.com/trainihttps://apis.garmin.com/training-api/schedule?stng-api/schedule?startDate=YYYY-mm-artDate=YYYY-mm-
dd&endDate=YYYY-mm-dddd&endDate=YYYY-mm-dd
Response Body: An array of workout schedules as JSOResponse Body: An array of workout schedules as JSON.N.
```
Response:Response:

HTTP HTTP Response Response Status Status DescriptionDescription

```
200 200 Workout Workout schedule schedule successfully successfully retrieved retrieved for for the the date date
range specifiedrange specified
```
401401 User Access Token doesn’t existUser Access Token doesn’t exist

412 412 User User permission permission errorerror

429429 Quota violation / rate‐limitingQuota violation / rate‐limiting

We and our 41 IAB TCF partners store and access information on your device for the following purposes: store and/or access information on a device, advertising and content

measurement, audience research, and services development, personalised advertising, and personalised content.

Personal data may be processed to do the following: use precise geolocation data and actively scan device characteristics for identication.

Our third party IAB TCF partners may store and access information on your device such as IP address and device characteristics. Our IAB TCF Partners may process this

personal data on the basis of legitimate interest, or with your consent. You may change or withdraw your preferences for this website at any time by clicking on the cookie

icon or link; however, as a consequence, you may not see relevant ads or personalized content.
Our website may use these cookies to:

```
Measure the audience of the advertising on our website, without proling
Display personalized ads based on your navigation and your prole
Personalize our editorial content based on your navigation
Allow you to share content on social networks or platforms present on our website
Send you advertising based on your location
```
Privacy Policy
Third Parties

Customize Your Choices

Accept All



