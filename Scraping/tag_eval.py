from database_handler import DatabaseCaller

dbcaller = DatabaseCaller()

query_terms = (
    'Engineering',
    'Mathematics',
    'Science',
    'Humanities',
    'Management',
    'Business',
    'Physics',
    'Language',
    'Economics',
    'Computer Science'
    )

match_pairs = {'Computer Science': ('Science', 'Engineering', 'Mathematics', 'Language'),
               'Language': ('Humanities', 'Linguistics', 'Computer Science'),
               'Spanish': ('Language',),
               'Physics': ('Engineering', 'Mathematics'),
               'Aerospace Engineering': ('Engineering', 'Mathematics'),
               'Business': ('Economics', 'Management', 'Humanities', 'Innovation'),
               'Economics': ('Business', 'Social Science'),
               'Entrepreneurship': ('Business',),
               'Management': ('Business', 'Innovation', 'Supply Chain Management', 'Humanities'),
               'Humanities': ('Social Science', 'Business', 'Language', 'Management'),
               'Sociology': ('Humanities',),
               'Psychology': ('Humanities',),
               'Fine Arts': ('Humanities',),
               'Cognitive Science': ('Humanities',),
               'Innovation': ('Business',),
               'Social Science': ('Management', 'Humanities', 'Science', 'Language', 'Economics'),
               'Science': ('Engineering', 'Physics', 'Biology', 'Computer Science', 'Economics'),
               'Mathematics': ('Engineering', 'Science', 'Physics', 'Business'),
               'Engineering': ('Science', 'Physics', 'Computer Science', 'Mathematics', 'Management')}

counted = 0
total_count = 0

file_dir_path = 'eval_results/'

for query_term in query_terms:
    # Get the associated file
    query_doc_ids = []
    with open("{}.txt".format(file_dir_path + query_term), 'r') as f:
        for line in f:
            line = line.split(',')[0]
            query_doc_ids.append(line)
    
    for doc_id in query_doc_ids:
        course_id = dbcaller.query("SELECT course_id FROM lecture_metadata WHERE lec_id={}".format(doc_id))
        course_id = int(course_id[0][0])
        source = dbcaller.query("SELECT source FROM course_metadata WHERE course_id={}".format(course_id))[0][0]
        if source == 'KHAN_ACADEMY':
            continue
        tags_for_doc = dbcaller.query("SELECT course_tag0, course_tag1, course_tag2 FROM course_metadata WHERE course_id={}".format(course_id))
        tags_for_doc = [x.strip() for x in tags_for_doc[0] if x is not None]
        # Match pairs
        new_tags_for_doc = set(tags_for_doc)
        for tag_for_doc in tags_for_doc:
            if tag_for_doc in match_pairs:
                for x in match_pairs[tag_for_doc]:
                    new_tags_for_doc.add(x)
        if query_term in new_tags_for_doc:
            counted += 1
        else:
            print("Expected: {}, Got: {}".format(query_term, tags_for_doc))
            pass
        total_count += 1


print("Counted: {} \nTotal count: {} \n Percentage: {:.2f}%".format(counted, total_count, 100*counted/total_count))