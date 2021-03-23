from __future__ import unicode_literals, print_function
import json
import logging
import pickle
import random
from pathlib import Path
import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example

class SpacyModel(object):
    def tsv_to_json_format(self,input_path,output_path,unknown_label):
        try:
            f=open(input_path,'r',encoding="utf8") # input file
            fp=open(output_path, 'w') # output file
            data_dict={}
            annotations =[]
            label_dict={}
            s=''
            start=0
            for line in f:
                if line[0:len(line)-1]!='.\tO':
                    word,entity=line.split('\t')
                    s+=word+" "
                    entity=entity[:len(entity)-1]
                    if entity!=unknown_label:
                        if len(entity) != 1:
                            d={}
                            d['text']=word
                            d['start']=start
                            d['end']=start+len(word)-1  
                            try:
                                label_dict[entity].append(d)
                            except:
                                label_dict[entity]=[]
                                label_dict[entity].append(d) 
                    start+=len(word)+1
                else:
                    data_dict['content']=s
                    s=''
                    label_list=[]
                    for ents in list(label_dict.keys()):
                        for i in range(len(label_dict[ents])):
                            if(label_dict[ents][i]['text']!=''):
                                l=[ents,label_dict[ents][i]]
                                for j in range(i+1,len(label_dict[ents])): 
                                    if(label_dict[ents][i]['text']==label_dict[ents][j]['text']):  
                                        di={}
                                        di['start']=label_dict[ents][j]['start']
                                        di['end']=label_dict[ents][j]['end']
                                        di['text']=label_dict[ents][i]['text']
                                        l.append(di)
                                        label_dict[ents][j]['text']=''
                                label_list.append(l)                          
                                
                    for entities in label_list:
                        label={}
                        label['label']=[entities[0]]
                        label['points']=entities[1:]
                        annotations.append(label)
                    data_dict['annotation']=annotations
                    annotations=[]
                    print(data_dict)
                    json.dump(data_dict, fp)
                    fp.write('\n')
                    data_dict={}
                    start=0
                    label_dict={}
        except Exception as e:
            logging.exception("Unable to process file" + "\n" + "error = " + str(e))
            return None

    def prepareTrainingData(self,input_file=None, output_file=None):
        try:
            training_data = []
            lines=[]
            with open(input_file, 'r') as f:
                lines = f.readlines()

            for line in lines:
                data = json.loads(line)
                text = data['content']
                entities = []
                for annotation in data['annotation']:
                    point = annotation['points'][0]
                    labels = annotation['label']
                    if not isinstance(labels, list):
                        labels = [labels]

                    for label in labels:
                        entities.append((point['start'], point['end'] + 1 ,label))


                training_data.append((text, {"entities" : entities}))

            print(training_data)

            with open(output_file, 'wb') as fp:
                pickle.dump(training_data, fp)

        except Exception as e:
            logging.exception("Unable to process " + input_file + "\n" + "error = " + str(e))
            return None

    def modelPreparation(self,model=None, new_model_name='new_model', output_dir=None, n_iter=10):
        """Setting up the pipeline and entity recognizer, and training the new entity."""
        with open ("E:/finalYearProject/code/testing_data_out.py", 'rb') as fp:
            TRAIN_DATA = pickle.load(fp)

        if model is not None:
            nlp = spacy.load(model)  # load existing spacy model
            #print("Loaded model '%s'" % model)
        else:
            nlp = spacy.blank('en')  # create blank Language class
            print("Created blank 'en' model")
        if 'ner' not in nlp.pipe_names:
            #ner = nlp.create_pipe('ner')
            nlp.add_pipe('ner')
            ner = nlp.get_pipe('ner')
        else:
            ner = nlp.get_pipe('ner')

        #for i in LABEL:
        #    print(i,"icecream")
        #    ner.add_label(i)   # Add new entity labels to entity recognizer

        if model is None:
            optimizer = nlp.begin_training()
        else:
            optimizer = nlp.entity.create_optimizer()

        # Get names of other pipes to disable them during training to train only NER
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
        with nlp.disable_pipes(*other_pipes):  # only train NER
            for itn in range(n_iter):
                random.shuffle(TRAIN_DATA)
                losses = {}
                batches = minibatch(TRAIN_DATA, size=compounding(4., 32., 1.001))
                for batch in batches:
                    texts, annotations = zip(*batch)
                    dummy=0
                    di={}
                    dil=[]
                    for texts, annotations in batch:
                        print(texts,annotations,"hiiiiii")
                        example = Example.from_dict(nlp.make_doc(texts), annotations)
                        nlp.update([example],drop=0.5,sgd=optimizer,losses=losses) 
        
            # Save model 
        if output_dir is not None:
            output_dir = Path(output_dir)
            if not output_dir.exists():
                output_dir.mkdir()
            nlp.meta['name'] = new_model_name  # rename model
            nlp.to_disk(output_dir)
            print("Saved model to", output_dir)


    def testing_func(self,output_dir,test_text):
        nlp2 = spacy.load(output_dir)
        #test_text="let me see all phones between 20,000 and 99,999"
        doc2 = nlp2(test_text)
        #print(doc2.ents)
        result_dic = {}
        for ent in doc2.ents:
            result_dic[ent.label_] = ent.text
            print(ent.label_,"===>", ent.text)
        
        return result_dic