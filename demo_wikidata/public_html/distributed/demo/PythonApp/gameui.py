import PySimpleGUI as sg

def choiceWindow(subject, relation, llm_objects, obj_ids, wikidata_objects, explanation):
	layout = [
        [sg.Text(f"Subject: {subject}", font=('Helvetica', 12))],
        [sg.Text(f"Relation: {relation}", font=('Helvetica', 12))],
        [sg.Text(f"LLM Response: {llm_objects}", font=('Helvetica', 12))],
        [sg.Text(f"Wikidata Mapping (IDs): {obj_ids}", font=('Helvetica', 12))],
        [sg.Multiline(f"Explanation: {explanation}", size=(40, 5), font=('Helvetica', 12), disabled=True)],
        [sg.HorizontalSeparator()],
        [sg.Button("Accept", size=(10, 2), font=('Helvetica', 12)), sg.Button("Reject", size=(10, 2), font=('Helvetica', 12))],
        [sg.HorizontalSeparator()],
        [sg.Text(f"Wikidata Response: {wikidata_objects}", font=('Helvetica', 12))],
    ]
    
    # Create the window
	window = sg.Window("Accept or Reject this statement", layout, element_justification='c', size=(600, 400))
	# Create an event loop
	end_flag = False
	accepted = False
	while True:
	    event, values = window.read()
	    # End program if user closes window or
	    # presses the buttons
	    if event == sg.WIN_CLOSED:
	    	end_flag = True
	    	break
	    elif event == "Accept":
	    	accepted = True
	    	break
	    elif event == "Reject":
	   		break
	window.close()
	return end_flag, accepted