export const USER_PROFILE_RESPONSE = {
  "filled_out": false,
  "agreed_to_terms_of_service": true,
  "account_privacy": "all_users",
  "email_optin": false,
  "first_name": "Jane",
  "last_name": "Garris",
  "preferred_name": "Jane Garris",
  "country": "US",
  "state_or_territory": "MA",
  "city": "Cambridge",
  "birth_country": "US",
  "birth_state_or_territory": "MA",
  "birth_city": "Cambridge",
  "has_profile_image": true,
  "profile_url_full": "http://192.168.33.10:8000/static/images/profiles/default_500.png",
  "profile_url_large": "http://192.168.33.10:8000/static/images/profiles/default_120.png",
  "profile_url_medium": "http://192.168.33.10:8000/static/images/profiles/default_50.png",
  "profile_url_small": "http://192.168.33.10:8000/static/images/profiles/default_30.png",
  "date_of_birth": '1984-04-13',
  "preferred_language": 'en',
  "gender": "f",
  "pretty_printed_student_id": "MMM000011"
};

export const STATUS_PASSED = 'passed';
export const STATUS_NOT_PASSED = 'not-passed';
export const STATUS_VERIFIED_NOT_COMPLETED = 'verified-not-completed';
export const STATUS_ENROLLED_NOT_VERIFIED = "enrolled-not-verified";
export const STATUS_OFFERED_NOT_ENROLLED = "offered-not-enrolled";
export const STATUS_NOT_OFFERED = 'not-offered';

export const DASHBOARD_RESPONSE = [
  {
    "title": "Empty program",
    "description": "The empty program",
    "courses": [
    ],
    "id": 2
  },
  {
    "courses": [
      {
        "id": 3,
        "status": STATUS_OFFERED_NOT_ENROLLED,
        "position_in_program": 1,
        "title": "Supply Chain and Logistics Fundamentals",
        "runs": [
          {
            "course_id": null,
            "id": 3,
            "status": STATUS_OFFERED_NOT_ENROLLED,
            "fuzzy_enrollment_start_date": null,
            "title": "Supply Chain Design",
            "enrollment_start_date": "2016-03-04T01:00:00Z"
          }
        ],
        "description": null,
        "prerequisites": null
      },
      {
        "id": 4,
        "status": STATUS_PASSED,
        "position_in_program": 0,
        "title": "Demo course",
        "runs": [
          {
            "certificate_url": "www.google.com",
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "id": 4,
            "status": STATUS_PASSED,
            "title": "Demo course",
            "grade": "0.88"
          }
        ],
        "description": "The demo course",
        "prerequisites": ""
      },
      {
        "id": 5,
        "status": STATUS_NOT_OFFERED,
        "position_in_program": 2,
        "title": "Empty course",
        "runs": [
        ],
        "description": null,
        "prerequisites": null
      },
    ],
    "title": "Master Program",
    "description": null,
    "id": 1
  },
  {
    "title": "Last program",
    "description": "The last program",
    "courses": [
      {
        "id": 4,
        "status": STATUS_VERIFIED_NOT_COMPLETED,
        "position_in_program": 0,
        "title": "Course for last program",
        "runs": [
          {
            "course_id": "course-v1:edX+DemoX+Demo_Course",
            "id": 4,
            "status": STATUS_VERIFIED_NOT_COMPLETED,
            "title": "Course run for last program"
          }
        ],
        "description": "Course for Last program",
        "prerequisites": ""
      },
    ],
    "id": 3
  },
];

export const HIGH_SCHOOL = 'hs';
export const ASSOCIATE = 'a';
export const BACHELORS = 'b';
export const MASTERS = 'm';
export const DOCTORATE = 'p';

export const DATE_FORMAT = 'YYYY-MM-DD';
