from fast_autocomplete import AutoComplete
from database_handler import DatabaseCaller
import dill

def load_auto_complete():
    dbcaller = DatabaseCaller()

    words_arr = dbcaller.query("SELECT lecture_title FROM lecture_metadata")
    words_arr.extend(dbcaller.query("SELECT course_title FROM course_metadata"))
    words = dict()
    for word in words_arr:
        # Filter the text a bit
        word = word[0].lower().strip()
        word = word.replace("pdf", "").replace("\n", "")
        # Remove anything in brackets
        temp = word.split("(")
        if len(temp) > 1 and len(temp[1].split(")")) > 1:
            word = temp[0] + temp[1].split(")")[1]
            word = word.strip()
        words[word] = {}

    synonyms = {
        "machine learning": ["ml"],
        "text technologies for data science": ["ttds", "search engine"],
    }

    return AutoComplete(words=words, synonyms=synonyms)

if __name__ == '__main__':
    # Pickle the object (this would be done offline)
    # autocomplete_pickled = "autocomplete"
    # with open(autocomplete_pickled, 'wb') as pickled_file:
    #     dill.dump(load_auto_complete(), pickled_file)

    # Load the pickled object (this would be done during inference time)
    autocomplete_pickled = "autocomplete"
    with open(autocomplete_pickled, 'rb') as pickled_file:
        autocomplete = dill.load(pickled_file)
        print(autocomplete.search(word='d', max_cost=5, size=3))
        print(autocomplete.search(word='da', max_cost=5, size=3))
        print(autocomplete.search(word='dat', max_cost=5, size=3))
        print(autocomplete.search(word='data', max_cost=5, size=3))
        print(autocomplete.search(word='datab', max_cost=5, size=3))
        print(autocomplete.search(word='databa', max_cost=5, size=3))
        print(autocomplete.search(word='database', max_cost=5, size=3))
        print("\n")
        print(autocomplete.search(word='computer', max_cost=5, size=3))