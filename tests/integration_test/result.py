from conftest import TEST_USER_ID

ANNOTATION = {
    "TEST_1": [
        {
            "annotation_list": [],
            "record_content": "criminal history is a background_screening",
            "record_metadata": [],
        },
        {
            "annotation_list": [],
            "record_content": "criminal background is a background_screening",
            "record_metadata": [],
        },
        {
            "annotation_list": [],
            "record_content": "criminal background check is a background_screening",
            "record_metadata": [],
        },
        {
            "annotation_list": [],
            "record_content": "criminal back ground is a background_screening",
            "record_metadata": [],
        },
        {
            "annotation_list": [],
            "record_content": "criminal record is a background_screening",
            "record_metadata": [],
        },
        {
            "annotation_list": [],
            "record_content": "criminal records is a background_screening",
            "record_metadata": [],
        },
        {
            "annotation_list": [],
            "record_content": "criminal charges is a background_screening",
            "record_metadata": [],
        },
    ],
    "TEST_4": [
        {
            "annotation_list": [
                {
                    "annotator": TEST_USER_ID,
                    "labels_record": [
                        {
                            "label_level": "record",
                            "label_metadata_list": [],
                            "label_name": "pair_validation",
                            "label_value": ["true"],
                        }
                    ],
                    "labels_span": [],
                }
            ],
            "record_content": "criminal history is a background_screening",
            "record_metadata": [],
        }
    ],
}

VIEWS = {
    "TEST_VIEW_RECORD_1": [
        {
            'record_content': 'criminal history is a background_screening', 
            'record_id': 1, 
            'record_metadata': [], 
        }, 
    ],
    "TEST_VIEW_ANNOTATION_1": [
            {
                'annotation_list':[
                    {
                        'labels_record': [{'label_level': 'record', 'label_metadata_list': [], 'label_name': 'pair_validation', 'label_value': ['true']}], 
                        'labels_span': []
                    }
                ], 
                
            }, 
    ],
    "TEST_VIEW_ANNOTATION_2": [
        {
            'annotation_list' : [
                {
                    'labels_record': [], 
                    'labels_span': []
                }
            ]
        }, 
    ],
    "TEST_VIEW_VERIFICATIONS_1": [
        {
            'verification_list' : []
        }, 
        {
            'verification_list' : []
        }, 
        {
            'verification_list' : []
        }
    ],
}
