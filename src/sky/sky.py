import re
import os
import pickle


from .utils import *
from .httpRequest import *
from logging import warn, warning


class Sky:
    def __init__(
        self,
        api_key: Union[str, None] = None,
        file_path: str = "sky_credentials.json",
        token_path: Union[str, None] = None,
        credentials: dict = None,
    ):
        """Blackbaud Sky API client

        This class uses a :class:`authlib.integrations.requests_client.OAuth2Session` for
        calls to the Blackbaud Sky API.

        """
        self.token = None
        self.client = None
        self.file_path = file_path
        self.credentials = credentials

        # Seeing if the user saved the api key as an environment variable
        if os.getenv("BB_API_KEY"):
            self.api_key = os.getenv("BB_API_KEY")
        elif api_key:
            self.api_key = api_key
        else:
            warn(
                """
            A api key is needed to call the Blackbaud sky api. You can either initialize it when calling
            the Sky class or you can save it in a environment variable called BB_API_KEY
            """
            )

        # Path to cached token
        if token_path:
            self.token_path = token_path
        elif os.getenv("BB_TOKEN_PATH"):
            self.token_path = os.getenv("BB_TOKEN_PATH")
        else:
            self.token_path = ".sky-token"

    @authorize
    def get(
        self,
        endpoint: str = "roles",
        params: Union[dict, None] = None,
        reference: str = "school",
        raw_data: bool = False,
    ) -> Union[dict, pd.DataFrame, dict, None]:
        """Get request to the Sky API
        Args:
            params: Dictionary that defines parameters to be passed to
            the api
            reference: Which SKY Api refrence are you calling. See them here
            https://developer.blackbaud.com/skyapi/apis
            endpoint: The specific endpioint that exist in the given api reference
        Returns:
           Dictionary with data from the sky api
        """
        url = self._get_url(reference, endpoint)
        df = pd.DataFrame()
        while True:
            # Calling API
            apiCall = GetRequest(self.client, url, self.request_header, params=params)
            data = apiCall.getData()
            self._saveToken(apiCall.updateToken(self.token))
            # Checking if user wants the raw dictionary
            if raw_data:
                return data
            if not data.get("value"):
                # Still returning df for single user endpoints
                if data:
                    if data.get("status") == 404 or data.get("errors"):
                        warn("ERROR: Invalid request")
                        return data
                    return pd.json_normalize(data)
                return None
            df = pd.concat([df, pd.json_normalize(data["value"])], ignore_index=True)
            # Checking for another link
            if not data.get("next_link"):
                return df
            # Saving the next link
            link = data["next_link"]
            # Finding the endpoint value
            end = re.search("v[\\d]/", link).end(0)
            url = self._get_url(reference, link[end:])

    @authorize
    def post(
        self,
        data: dict,
        reference: str = "school",
        endpoint: str = "users",
    ) -> dict:
        """Post request to the Sky API
        Args:
            data: Dictionary that defines the request data to be passed to
            the api in order to create a new record
            reference: Which SKY Api refrence are you calling. See them here
            https://developer.blackbaud.com/skyapi/apis
            endpoint: The specific endpioint that exist in the given api reference
        Returns:
           Dictionary with data from the sky api
        """
        url = self._get_url(reference, endpoint)

        apiCall = PostRequest(self.client, url, self.request_header, data=data)

        data = apiCall.getData()
        self._saveToken(apiCall.updateToken(self.token))
        return data

    @authorize
    def patch(
        self,
        reference: str = "school",
        endpoint: str = "users",
        params: Union[dict, None] = None,
        body: Union[dict, None] = None,
        data: Union[dict, None] = None,
        **kwargs,
    ) -> dict:
        """Patch requests to the Sky API
        Args:
            data: Dictionary that defines the request data to be passed to
            the api in order to create a new record
            reference: Which SKY Api refrence are you calling. See them here
            https://developer.blackbaud.com/skyapi/apis
            endpoint: The specific endpioint that exist in the given api reference
        Returns:
           Dictionary with data from the sky api
        """
        url = self._get_url(reference, endpoint)

        apiCall = PatchRequest(
            self.client, url, self.request_header, params=params, data=data
        )

        data = apiCall.getData(**kwargs)
        self._saveToken(apiCall.updateToken(self.token))
        return data

    @authorize
    def delete(
        self,
        reference: str = "school",
        endpoint: str = "roles",
        params: Union[dict, None] = None,
        data: Union[dict, None] = None,
        **kwargs,
    ) -> dict:
        """Delete requests to the sky API

        Args:
            reference: Which SKY Api refrence are you calling. See them here
            https://developer.blackbaud.com/skyapi/apis
            endpoint: The specific endpioint that exist in the given api reference
            **kwargs: ... Honestly don't know yet. Never used this endpoint. Just
            adding for testing
        Returns:
           Dictionary with data from the sky api
        """
        url = self._get_url(reference, endpoint)

        apiCall = DeleteRequest(
            self.client, url, self.request_header, params=params, data=data
        )

        data = apiCall.getData(**kwargs)
        self._saveToken(apiCall.updateToken(self.token))
        return data

    def getUsers(self, roles: Union[list, str] = "student") -> pd.DataFrame:
        """Get a DataFrame of users from the Core database

        Args:
            roles: A list (or string) of role name(s) from your Blackbaud
            Core database
        Returns:
            Pandas dataframe of users details
        """
        roles = self.getRoleId(roles)
        users = pd.DataFrame()
        for role in roles:
            user_df = self.get(
                endpoint="users/extended", params={"base_role_ids": role}
            )
            if isinstance(user_df, pd.DataFrame):
                users = pd.concat([users, user_df], ignore_index=True)
        return users

    def getRoleId(self, roles: Union[list, str], base: bool = True) -> int:
        """Get the Blackbaud id of a role in the Core database

        Args:
            role_name: Name of a role in Core
            base: If True the base_role_id is returned, otherwise the role id
            is returned

        Returns:
            The id of a given role
        """
        if isinstance(roles, str):
            roles = [roles]
        # Each role should have Title case to match Blackbaud
        for i in range(len(roles)):
            roles[i] = roles[i].title()
        role_id = self.get("roles")
        role_id = role_id.loc[role_id.name.isin(roles)]
        # Returning the base
        if base:
            return role_id.base_role_id.tolist()
        return role_id.id.tolist()

    def getLevels(
        self, abbv: str = None, name: str = None, id: bool = False
    ) -> Union[pd.DataFrame, list, int]:
        """Gets school level data from Core database

        Args:
            abbreviation: Abbreviation of a given school level in the Core db
            name: Name of a given school level in the Core db
            id: If True only the levels id will be returned

        Returns:
            Either a df of the school level(s) in the Core db or just the
            given level's id
        """
        # Calling sky to get levels
        levels = self.get("levels")
        # Filtering
        if abbv:
            levels = levels.loc[
                (levels.abbreviation == abbv),
            ]
        elif name:
            levels = levels.loc[
                (levels.name == name),
            ]

        # Either returning levels df or just the id value of a particular school level
        if id:
            return levels.id.values.tolist()
        return levels

    def getSections(
        self,
        abbv: str = None,
        name: str = None,
    ) -> pd.DataFrame:
        """Gets the sections in the users Core database

        Args:
            abbreviation: Abbreviation of a given school level in the Core db
            to be passed into self.getLevels
            name: Name of a given school level in the Core db to be passed
             into self.getLevels

        Returns:
            Dataframe with data from sections in the Core Db
        """

        course_levels = self.getLevels(name=name, abbv=abbv, id=True)

        df = pd.DataFrame()

        # Passing level_ids to the Sky API
        for level in course_levels:
            # Appending data to the df
            df = pd.concat(
                [
                    df,
                    self.get(
                        endpoint="academics/sections", params={"level_num": level}
                    ),
                ],
                ignore_index=True,
            )

        # Cleaning the teacher data for each section
        teacher_data = (
            df.explode("teachers")["teachers"]
            .apply(pd.Series)
            .query("head == True")
            .add_prefix("teacher.")
            .drop("teacher.0", axis=1)
        )

        # Merging sections with the teachers
        df = (
            df.merge(teacher_data, left_index=True, right_index=True)
            .reset_index(drop=True)
            .drop("teachers", axis=1)
        )

        return df

    def getStudentEnrollments(self, students: Union[int, list] = None) -> pd.DataFrame:
        """Returns a DataFrame of all current student enrollments"""
        if not students:
            students = self.getUsers()
            students = students.id.tolist()
        if isinstance(students, (str, int)):
            students = [students]
        if not isinstance(students, list):
            raise Exception(
                "Value of students must either be a user id or list of user ids"
            )

        enrollment = pd.DataFrame()
        for user_id in students:
            student_enrollment = self.get(f"academics/enrollments/{user_id}")
            if isinstance(student_enrollment, pd.DataFrame):
                student_enrollment = student_enrollment.assign(user_id=user_id)
                enrollment = pd.concat(
                    [enrollment, student_enrollment], ignore_index=True
                )
        return enrollment

    def enrollmentMedley(
        self,
    ) -> dict:

        # Getting current school year enrollments
        enrollments = self.getStudentEnrollments()

        # Getting the level description of the enrollments
        enrollments = enrollments.merge(
            self.getLevels()
            .drop("abbreviation", axis=1)
            .rename(columns={"id": "level_number", "name": "level_description"})
        )

        # Saving offerings db once instead of calling for each id
        offerings = self.get("offeringtypes")

        # Filtering enrollments for advisory and academic enrollments
        academic_enrollments = enrollments.loc[
            enrollments.offering_type_id.isin(
                offerings.loc[offerings.description == "Academics", "id"].tolist()
            )
        ]
        advisory_enrollments = enrollments.loc[
            enrollments.offering_type_id.isin(
                offerings.loc[offerings.description == "Advisory", "id"].tolist()
            )
        ]

        advisory_enrollments = advisory_enrollments.loc[
            advisory_enrollments.changed_sections == 0
        ]

        # Cleaning the department names
        departments = (
            academic_enrollments.departments.explode()
            .apply(pd.Series)
            .drop([0, "id"], axis=1)
            .rename(columns={"name": "department_name"})
        )

        # Removing departments from the academic df
        academic_enrollments = academic_enrollments.drop("departments", axis=1)

        # Adding dept. name to the academic df
        academic_enrollments = academic_enrollments.merge(
            departments, left_index=True, right_index=True
        )

        # Cleaning the Academic Enrollments
        term = self.getTerm(active=True, offeringType="Academics")[0].split(" ")[0]
        academic_enrollments = (
            academic_enrollments.loc[
                academic_enrollments.duration_name == term,
                [
                    "user_id",
                    "block_name",
                    "course_title",
                    "faculty_first_name",
                    "faculty_last_name",
                    "duration_name",
                    "id",
                    "department_name",
                    "section_identifier",
                ],
            ]
            .rename(columns={"id": "section_id"})
            .dropna(axis=0, subset=["section_id"])
        )

        # Cleaning advisory enrollments
        advisory_enrollments = advisory_enrollments.loc[
            advisory_enrollments.changed_sections == 0
        ]
        # Getting the active term
        term = self.getTerm(active=True, offeringType="Advisory")[0].split(" ")[0]
        advisory_enrollments = (
            advisory_enrollments.loc[
                advisory_enrollments.duration_name == term,
                [
                    "user_id",
                    "course_title",
                    "faculty_first_name",
                    "faculty_last_name",
                    "id",
                ],
            ]
            .rename(columns={"id": "section_id"})
            .dropna(axis=0, subset=["section_id"])
        )

        # Cleaning athletic enrollments
        athletics_enrollments = (
            enrollments.loc[
                enrollments.offering_type_id.isin(
                    offerings.loc[offerings.description == "Athletic", "id"].tolist()
                ),
                [
                    "user_id",
                    "course_title",
                    "faculty_first_name",
                    "faculty_last_name",
                    "id",
                    "duration_name",
                ],
            ]
            .rename(columns={"id": "section_id"})
            .dropna(axis=0, subset=["section_id"])
        )

        enrollment_dict = {
            "academics": academic_enrollments,
            "advisory": advisory_enrollments,
            "athletics": athletics_enrollments,
        }

        return enrollment_dict

    def getTerm(
        self, offeringType: str = "Academics", active=False
    ) -> Union[pd.DataFrame, list, str]:
        """Gets the active terms for the given offering type

        Args:
            offeringType: A string of a Core offering type
            active: If true just the name of the active terms wil be returned
        Returns:

        """
        params = {"offering_type": self.getOfferingId(offeringType)[0]}

        data = self.get("terms", params=params)[
            ["id", "level_description", "description", "begin_date", "end_date"]
        ]

        data = data.query("id > 0").reset_index(drop=True)
        data["begin_date"] = pd.to_datetime(data["begin_date"])
        data["end_date"] = pd.to_datetime(data["end_date"])

        active_terms = isActiveTerm(data).rename(
            columns={"id": "term_id", "description": "term_name"}
        )[["term_id", "term_name", "active"]]

        # Returning the name of the active term(s)
        if active:
            active_terms_list = (
                active_terms.loc[active_terms["active"] == True, "term_name"]
                .drop_duplicates()
                .tolist()
            )
            return active_terms_list
        return active_terms

    def getOfferingId(self, offeringType: Union[str, list] = "Academics") -> list:
        """Gets the id of a Core offering type"""
        if isinstance(offeringType, str):
            offeringType = [offeringType]
        data = self.get("offeringtypes")
        return data.loc[data.description.isin(offeringType), "id"].tolist()

    def getAdvancedList(self, list_id: int) -> pd.DataFrame:
        """Gets Advanced list from Core

        Args:
            list_id: The sld of an advanced list in Core

        Returns:
            A pandas dataframe of the advanced list
        """
        # Calling api to get raw list data (Updated the URL as of 1/1/23)
        raw_list = self.get(endpoint=f"lists/advanced/{list_id}", raw_data=True)
        # Type casting the data to a dataframe

        data = pd.json_normalize(raw_list["rows"], "columns").reset_index()
        return cleanAdvancedList(data)

    def _loadCachedToken(self) -> Union[None, OAuth2Token]:
        """Load Sky API token from cache"""
        # Loading token from binary file
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                self.token = pickle.load(token)
        return self.token

    def _get_url(self, reference: str, endpoint: str) -> str:
        """Format api requests url

        Args:
            reference:
            endpoint:

        Returns:
            API url to call
        """
        return f"https://api.sky.blackbaud.com/{reference}/v1/{endpoint}"

    def _saveToken(self, token: OAuth2Token) -> None:
        """Save OAuth2Token for future use"""
        with open(self.token_path, "wb") as f:
            pickle.dump(token, f)
        self.token = token

    @property
    def request_header(self):
        """API key to pass to Request header"""
        return {"Bb-Api-Subscription-Key": self.api_key}
