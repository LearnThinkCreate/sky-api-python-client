# sky-api-python-client

A lightweight, easy to use, Python library for communicating with the Blackbaud Sky API

## About

This is a python library for connecting the [Blackbaud Sky API](https://developer.blackbaud.com/skyapi/). Behind the scenes the Blackbaud SKY API uses [Authorization Code Flow](https://developer.blackbaud.com/skyapi/docs/authorization/auth-code-flow), which requires the client ID and client secret to get a refresh token and make API calls. The goal of the sky-api-python-client is to abstract details from the OAuth2.0 process so the user can get to coding as quickly as possible.

To authenticate with the Blackbaud SKY API you will need a valid client_id, client_secret, and redirect_uri. If you are unsure how to get that information please see the section on [SKY API requirements](https://github.com/LearnThinkCreate/sky-api-python-client#sky-api-requirements).

The library itself is a wrapper around the `authlib` and `requests` python libraries. Authlib is used to establish a OAuth2Session, while requests handle the calls to the SKY API. A binary file is used to store your OAuth2Token in between sessions so that this library can be used in non-interactive sessions.

See Blackbaud's documentations on specific [references](https://developer.blackbaud.com/skyapi/apis) and [endpoints](https://developer.sky.blackbaud.com/docs/services/school/operations/v1usersget) that can be passed as arguments in api calls.

## Installing sky-api-python-client and setting up your working directory
- Install the latest version of the sky-api-python-client by running `python -m pip install --upgrade sky-api-python-client`
- Configure a sky_credentials.json file in your working directory. You can use the [sky_credentials_template.json](https://github.com/LearnThinkCreate/sky-api-python-client/blob/main/template.json) file for reference. 
    - By default the Sky class looks for a sky_credentials.json file. You can name it something else but you must pass in the new value into the `file_path` argument when initializing `Sky`.
- **Alternatively, if you'd like to store all of your credentials in your local environment, you can do that as well**
    - To do so, pass a dictionary to the `credentials` arg when calling `Sky`
    - [example of loading `Sky` with custom api_key, token_path, and credentials args](https://github.com/LearnThinkCreate/sky-reports/blob/main/config.py) 
- I highly recommend either saving your credentials in either a .env file of something similar 
    - Please see the example above or go to the [python-dotenv documentation](https://pypi.org/project/python-dotenv/#getting-started).
    - When called Sky will automatically check if there's a value for `BB_API_KEY` in your local environment

## Getting Started 
- Once sky-api-python-client is installed you can go directly into coding, even if you have not authorized your app yet.
    - The first time that any Sky request is sent (get, post, patch or delete) the sky-api-python-client will check the `token_path` for a valid API token. If it finds one it will proceed with the HTTP request. Otherwise it will check the `file_path` for a valid .json file with your Blackbaud credentials. 
- If Blackbaud credentials are found your default web browser will open and you will be asked to authorize your application. If your sky_crendtials are valid (the client_id, client_secret, and redirect_uri matches what's on your [application page](https://developer.blackbaud.com/apps/)) the sky-api-python-client will retrieve a access & refresh token on your behalf and save them for future use in a binary file located on your `token_path`. Otherwise the call will be executed without needing any user interaction


## Loading Sky

### Loading Sky and load_dotenv
```python
from sky import Sky
from dotenv import load_dotenv

# Loading BB_API_Key from .env file
load_dotenv()

client = Sky(
    api_key=None,
    file_path='sky_credentials.json',
    token_path=".sky-token"
  )
```

### Loading Sky from Environment Variables
``` Python
import os

from sky import Sky

# Starting sky client
sky = Sky(
    api_key=os.getenv('BB_API_KEY'),
    token_path='/tmp/.sky-token',
    credentials={
        "client_id":os.getenv('CLIENT_ID'),
        "client_secret":os.getenv('CLIENT_SECRET'),
        "redirect_uri":'http://localhost:8080'
    })
```

## API Request

### Sending a GET Request
```Python
roles = client.get().head(5)
roles
      id  base_role_id  hidden                    name
0  67454             1   False          Academic Chair
1  58802           523   False  Academic Group Manager
2  66719         10211   False  Academic Holds Manager
3  66648             2   False       Academic Platform
4  58820          3177   False  Activity Group Manager
```

### Sending a POST Request
```Python
new_user = client.post(data = {
      "first_name": "API",
      "last_name": "User"
    })
id = int(new_user.text)
id
5039522
```

### Sending a PATCH Request
```Python
update_user = client.patch(data={
      "id": id,
      "last_name": "NewUser"
    })
update_user.satus_code
200
```

## Core Helper Functions

### Getting Core Users by Role Name 
```Python
client.getUsers(role='student').head(5) 
        id  ... student_info.grade_level_description
0  4723944  ...                           12th Grade
1  4748327  ...                            9th Grade
2  4748330  ...                           12th Grade
3  4748334  ...                           10th Grade
4  4748337  ...                           12th Grade

[5 rows x 64 columns]

# Passing in list 
client.getUsers(['student', 'teacher']).head(5) 
        id  ... student_info.grade_level_description
0  4723944  ...                           12th Grade
1  4748327  ...                            9th Grade
2  4748330  ...                           12th Grade
3  4748334  ...                           10th Grade
4  4748337  ...                           12th Grade

[5 rows x 64 columns]
```

### Getting Academic Sections 
```Python
client.getSections().head(5)
         id course_code  ...  teacher.id      teacher.name
0  88981433    ARTS0612  ...   4748305.0  Martha DeAmbrose
1  88981433    ARTS0612  ...   4748305.0  Martha DeAmbrose
2  89093661    ARTS1303  ...   4748305.0  Martha DeAmbrose
3  89093661    ARTS1303  ...   4748305.0  Martha DeAmbrose
4  89092355    ARTS0612  ...   4748305.0  Martha DeAmbrose

[5 rows x 14 columns]
```

### Getting student Enrollments 
``` Python 
client.getStudentEnrollments(4750432)
            id                     begin_date  ...  section_identifier  user_id
0   89077321.0      2021-07-26T00:00:00-04:00  ...                   3  4750432
1   89077241.0      2021-07-26T00:00:00-04:00  ...                   1  4750432
2   89077271.0      2021-07-26T00:00:00-04:00  ...                   4  4750432
3   89077355.0      2021-07-26T00:00:00-04:00  ...                   2  4750432
4   89077299.0      2021-07-26T00:00:00-04:00  ...                   2  4750432
5   89077225.0      2021-07-26T00:00:00-04:00  ...                   1  4750432
6   89077322.0      2022-01-03T00:00:00-05:00  ...                   3  4750432
```

### Getting Academic, Advisory, and Athletic Enrollments
```Python
client.enrollmentMedley()
{
'academics': 
        user_id block_name  ...            department_name section_identifier
1      4723944         P1  ...                        NaN              21.22
18     4748327         P1  ...                    History                  6
19     4748327         P2  ...                    English                  1
20     4748327         P3  ...  Middle School Mathematics                  1
20     4748327         P3  ...   Upper School Mathematics                  1
...        ...        ...  ...                        ...                ...
15219  4944563         P4  ...                    English                  3
15220  4944563         P5  ...                       Arts           Calandra
15221  4944563         P5  ...                       Arts                Hoy
15222  4944563         P6  ...                    Science                  3
15232  4988484         P1  ...                        NaN              21.22

[5223 rows x 9 columns], 
'advisory':
        user_id         course_title  ... faculty_last_name  section_id
28     4748327   Advising 9 Chapman  ...           Chapman  89102628.0
49     4748330  Advising 12 Carlson  ...           Carlson  89102460.0
71     4748337  Advising 12 Carlson  ...           Carlson  89102460.0
95     4748339     Advising 10 Quah  ...              Quah  89102364.0
116    4748342   Advising 11 Keller  ...            Keller  89102424.0
...        ...                  ...  ...               ...         ...
15141  4932603   Advising 6 Hendrix  ...           Hendrix  89102526.0
15161  4936908    Advising 7 Henton  ...            Henton  89102568.0
15184  4939114    Advising 6 Bahtic  ...            Bahtic  89102514.0
15205  4939116     Advising 6 Seary  ...             Seary  89102538.0
15226  4944563     Advising 6 Seary  ...             Seary  89102538.0

[704 rows x 5 columns], 
'athletics':        
        user_id               course_title  ...  section_id duration_name
50     4748330           Varsity Bowling   ...  89122871.0          Fall
74     4748337                     Track   ...  89224901.0        Spring
119    4748342                   Lacrosse  ...  89231955.0        Spring
164    4748355             JV Boys Soccer  ...  89194214.0        Winter
165    4748355               Tennis- Boys  ...  89224950.0        Spring
...        ...                        ...  ...         ...           ...
15208  4939116              SHAC - Spring  ...  89100590.0        Spring
15227  4944563        Boy's Soccer - Fall  ...  89099033.0          Fall
15228  4944563     Boys Soccer- Gold Team  ...  89127428.0          Fall
15229  4944563  Boy's Basketball - Winter  ...  89100582.0        Winter
15230  4944563       Rowing/Crew - Spring  ...  89100592.0        Spring

[961 rows x 6 columns]}
```
### Getting an Advanced List From Core
```Python
client.getAdvancedList(73113).head(5).drop('email', axis=1)
name                   dob enrollDate firstname  ... locker studentId   userId
index                                            ...
1                      NaN        NaN    IGNORE  ...    NaN       NaN  4723944
2      08/22/2007 00:00:00        NaN   Emillie  ...   3153      6078  4748327
3      06/07/2004 00:00:00        NaN     Lukas  ...    NaN      6055  4748330
4      12/09/2005 00:00:00        NaN       Jos  ...   2078      6082  4748334
5      08/22/2009 00:00:00        NaN     Kylee  ...    NaN      6069  4748335

[5 rows x 11 columns]
```

### Getting Role Ids
``` Python
client.getRoleId('student')
[14]
client.getRoleId(['student', 'teacher'])
[14, 15]
```

### Getting School levels
``` Python
client.getLevels()
     id abbreviation           name
0  1940           MS  Middle School
1  1941           US   Upper School
2  1853        Entir  Entire School

client.getLevels(abbv='US', name='Upper School', id=True)
[1941]

```

### Getting academic terms
```Python
client.getTerm()
   term_id        term_name  active
0   100968    Fall Semester    True
1   100969  Spring Semester   False
2   100974    Fall Semester    True
3   100975  Spring Semester   False

client.getTerm(offeringType='Academics', active=True)
['Spring Semester']
 ```

### Getting offering ID
``` Python
client.getOfferingId(offeringType = 'Academics')
[1]

sky.getOfferingId(['Academics', 'Advisory'])
[1,3]
```

## SKY API requirements

- **A Blackbaud Developer subscription key**
    - If you have not already done so, complete the [Getting started guide](https://developer.blackbaud.com/skyapi/docs/getting-started). This will walk you through the process of registering for a Blackbaud developer account and requesting a subscription to an API product.
    - Once approved, your subscription will contain a **primary key** and **secondary key**. You can either pass the value of the API key directly into your script or you can save it in a environment variable call **BB_API_KEY**.
    - You can view your subscription keys on your [Blackbaud Developer profile](https://developer.sky.blackbaud.com/developer).
- **A Blackbaud Developer application ID and application secret**
    - [Register your application](https://developer.blackbaud.com/apps/) in order to obtain the **application ID** (client ID) and **application secret** (client secret).
    - When you call the Blackbaud Authorization Service from your application, you pass the `redirect_uri` as part of the call. The Blackbaud Authorization Service redirects to this URI after the user grants or denies permission. Therefore, you must whitelist the web address(es) or the authorization will fail.
    - URIs must _exactly_ match the value your application uses in calls to the Blackbaud Authorization Service.


