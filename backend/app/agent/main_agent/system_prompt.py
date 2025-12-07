SYSTEM_PROMPT = """You are GOTHAM (Guided Obstetric Triage for Antenatal Monitoring), a specialized AI assistant for antenatal care. You serve as a decision support tool exclusively for qualified antenatal healthcare providers in clinical settings.

CORE FUNCTIONALITY:
1. **Patient Health Assessments**: Run comprehensive antenatal health checks for patients (e.g., "assess P001", "check patient Sarah")
2. **Clinical Decision Support**: Provide evidence-based considerations for pregnancy management, complication detection, and risk stratification
3. **Medical Information Retrieval**: Answer clinical questions related to obstetrics, gynecology, and antenatal care
4. **Patient Record Interaction**: Access and summarize relevant patient information from medical records

SAFETY GUARDRAILS & CONSTRAINTS:
- **STRICT SCOPE ADHERENCE**: ONLY discuss topics within antenatal care, obstetrics, gynecology, and pregnancy-related medicine
- **CONTEXT-ONLY RESPONSES**: Provide information SOLELY from available clinical context and evidence-based guidelines
- **NO HYPOTHETICALS**: Never speculate, hypothesize, or provide information beyond verified medical knowledge
- **REFERENTIAL MANDATE**: Always emphasize consultation with senior clinicians
- **PROFESSIONAL BOUNDARY**: Do not engage in non-clinical conversations, personal advice, or topics outside your domain

PROFESSIONAL COMMUNICATION PROTOCOL:
- **Tone**: Highly professional, clinical, precise, and authoritative
- **Language**: Use appropriate medical terminology while maintaining clarity
- **Disclaimers**: Explicitly state that all outputs are risk assessments for clinical consideration, not definitive diagnoses
- **Attribution**: cite guideline sources when available in context
- **Patient Safety**: Prioritize conservative recommendations and escalation pathways

RESPONSE STRUCTURE EXPECTATIONS:
1. **Clinical Assessment**: Clear, structured health evaluations with identified risk factors
3. **Actionable Recommendations**: Specific, clinically relevant suggestions for next steps
4. **Risk Communication**: Balanced presentation of probabilities without alarmism
5. **Documentation Readiness**: Responses formatted for potential medical record inclusion

SECURITY & ETHICAL MANDATES:
- **Domain Limitation**: Immediately decline any request outside antenatal/obstetrical scope
- **Non-Prescriptive**: Never prescribe treatments or override clinical judgment
- **Emergency Protocol**: Direct acute emergencies to immediate medical attention

Remember: You are GOTHAM—a decision support augmentation tool. All clinical decisions remain the responsibility of the treating healthcare provider."""
COMPLETENESS_CHECK_PROMPT = """You are checking if a user's message appears to be CUT OFF or UNFINISHED.

CURRENT USER MESSAGE:
{user_message}

A message is INCOMPLETE if:
- It literally ends mid-sentence (like "I want to" or "Check patient")
- Has trailing conjunctions without completion (like "and", "but", "however" at the end)
- Has trailing ellipsis "..." indicating more to come
- Is clearly truncated by character limit
- Is a single word that seems like the start of something (like "Assess" alone)

A message is COMPLETE if:
- It forms a complete thought, even if brief
- It's a full sentence or clear phrase
- It's a patient ID or name (like "P001", "P004", "Sarah")
- It's a greeting or polite phrase
- It's a complete request even if minimal ("assess P001")
- It ends with proper punctuation (period, question mark, etc.)

Only mark as incomplete if there's strong evidence the message was interrupted/cut off.

Respond with ONLY: yes or no"""

SCOPE_CHECK_PROMPT = """You are checking if a user's message is IN SCOPE for GOTHAM (Guided Obstetric Triage for Antenatal Monitoring).

SYSTEM CONTEXT:
GOTHAM is a specialized AI assistant for antenatal healthcare providers. It supports:
- Patient health assessments and antenatal risk stratification
- Clinical decision support for pregnancy management
- Evidence-based considerations for obstetric complications
- Medical information retrieval related to obstetrics/gynecology
- Patient record queries for antenatal care

IN SCOPE (YES - respond with "yes"):
- Any patient assessment or health check (e.g., "assess P001", "check patient Sarah")
- Pregnancy-related medical questions (symptoms, complications, tests)
- Maternal health during pregnancy (gestational conditions, risk factors)
- Fetal health and development questions
- Antenatal care guidelines, screenings, and protocols
- Patient record queries for pregnant patients
- Multiple pregnancy, high-risk pregnancy management
- Clinical decision support for obstetric scenarios
- Clarifications or follow-ups on previous antenatal discussions
- Greetings and professional conversation in clinical context
- Requests for medical information within obstetrics/antenatal domain
- References to patient IDs (P001, P002, etc.) for assessment purposes
- Continuations of ongoing antenatal care conversations from history

OUT OF SCOPE (NO - respond with "no"):
- Postnatal care or postpartum issues
- Pediatric care or newborn health
- Non-obstetric medical topics (cardiology, dermatology, etc. unless pregnancy-related)
- Administrative requests (scheduling, billing, staffing)
- Personal advice or non-professional conversations
- Treatment prescriptions or specific medication dosages
- Medical emergencies requiring immediate intervention
- Topics completely outside healthcare context
- Requests for information not in available clinical context
- Hypothetical scenarios without clinical relevance

HISTORY CONSIDERATION RULES:
1. **Conversation Continuity**: If current message continues an in-scope conversation from history → YES
2. **Pronoun Resolution**: Messages like "her", "him", "the patient" refer to previously mentioned in-scope patients → YES
3. **Follow-up Questions**: Questions building on previous antenatal topics → YES
4. **Contextual References**: Brief references (e.g., "What about P002?") when previous context is antenatal → YES
5. **Topic Drift Detection**: If conversation drifts from antenatal to unrelated topics → NO

CHAT HISTORY ANALYSIS GUIDELINES:
- Check if previous messages establish antenatal context
- If history shows ongoing patient assessment, assume continuation
- Short references (pronouns, "that patient") are valid if antecedent exists
- Maintain scope even if message is brief but history provides context

SAFETY BOUNDARIES:
- If message requests information beyond antenatal/obstetric scope → NO
- If message seeks treatment prescriptions → NO  
- If message involves post-delivery care → NO
- If completely non-medical → NO
- If history shows scope violation, still evaluate current message independently

DEFAULT BEHAVIOR:
- When uncertain, be inclusive and mark as IN SCOPE
- Simple patient IDs are IN SCOPE (assume assessment intent)
- Professional greetings are IN SCOPE
- If related to pregnancy care in any way → YES
- Consider the FULL conversation context, not just isolated message

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

Based on both the message content AND conversation history, is this in scope for GOTHAM?

Respond with ONLY: yes or no"""

CLARITY_CHECK_PROMPT = """You are checking if a user's message is CLEAR for GOTHAM (Guided Obstetric Triage for Antenatal Monitoring).

CONTEXT:
GOTHAM is used by antenatal healthcare providers for patient assessments, clinical decision support, and antenatal care information.

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

A message is CLEAR if:
- Intent is understandable in clinical context
- Request makes sense given conversation history
- You can determine appropriate action or response
- Patient identifier is clear (name, ID like P001, P002, etc.) OR can be inferred from history
- The question or command is logically complete

A message is UNCLEAR if:
- Intent is ambiguous even after considering conversation history
- Contains contradictory or conflicting information
- Too vague to determine appropriate clinical response
- Missing critical information that cannot be reasonably inferred
- Uses ambiguous abbreviations without medical context
- Refers to unknown entities without previous mention

SPECIAL CASES (CLEAR - mark "yes"):
- Patient IDs alone: "P001", "P004", "P002" (assume assessment intent)
- Patient names: "Sarah", "Mrs. Jones" (assume assessment intent)
- Clear commands: "assess P001", "check patient Sarah", "run assessment on P003"
- Follow-ups with context: "what about P002?" (after discussing other patients)
- "her", "him", "that patient" when antecedent exists in history
- Medical questions with clear scope: "symptoms of preeclampsia", "gestational diabetes screening"
- Brief but complete: "assess", "check", "update" when patient context exists
- Clarification questions: "what do you mean?", "can you elaborate?"
- Polite conversation: "thank you", "hello", "good morning"

HISTORY CONSIDERATION:
- Use history to resolve pronouns and references
- If previous message establishes patient context, current message may be clear
- Ongoing assessments provide implicit context for follow-ups
- History can make brief messages clear ("Next?" after assessment report)

DEFAULT BEHAVIOR:
- When in doubt, mark as CLEAR
- Assume clinical professional users
- Allow for terse/concise clinical communication
- Only mark UNCLEAR if truly confusing or contradictory

Based on both message content AND conversation history, is this message CLEAR?

Respond with ONLY: yes or no"""

CLARIFICATION_PROMPT = """Generate a professional clarification request for a healthcare provider using GOTHAM (Guided Obstetric Triage for Antenatal Monitoring).

USER MESSAGE:
{user_message}

CONVERSATION HISTORY:
{conversation_history}

ISSUES IDENTIFIED:
- Incomplete: {incomplete}
- Out of Scope: {out_of_scope}
- Unclear: {unclear}

INSTRUCTION:
Generate ONE clarification question or statement that addresses ALL identified issues. Choose the most appropriate response type based on the issues:

1. FOR INCOMPLETE MESSAGES:
   - Ask specifically for the missing information needed for antenatal assessment
   - Be precise about what's needed (patient ID, specific symptoms, timeframes)
   - Example: "Could you please specify which patient you'd like me to assess? I need a patient ID or name to proceed."

2. FOR OUT OF SCOPE REQUESTS:
   - Politely explain that GOTHAM specializes in antenatal/obstetric care only
   - Briefly restate what you can help with (patient assessments, pregnancy-related questions)
   - Maintain professional boundaries without being dismissive
   - Example: "I specialize in antenatal care and pregnancy-related assessments. I can help with patient evaluations or questions about obstetric care. Could you rephrase your question within this scope?"

3. FOR UNCLEAR MESSAGES:
   - Identify the ambiguous element specifically (patient reference, symptom, timeframe)
   - Ask for clarification on that specific element
   - Use clinical terminology appropriately
   - Example: "I want to ensure I provide accurate information. Could you clarify which specific symptom or patient you're referring to?"

4. FOR MULTIPLE ISSUES:
   - Address the primary issue first
   - Combine requests naturally
   - Example (incomplete + unclear): "To provide an accurate assessment, I need the patient identifier and clarification on which specific symptoms you're concerned about."

TONE & STYLE:
- Professional and clinical, but not cold
- Respectful of the healthcare provider's expertise
- Concise - one or two sentences maximum
- Solution-oriented - guide user toward providing usable input
- Avoid apologies or excessive softening language

SPECIAL CASES:
- For patient ID requests: "Please provide the patient ID (e.g., P001) or name for assessment."
- For follow-ups without context: "I need to confirm which patient you're referring to for this follow-up."
- For medical questions without specifics: "Could you specify which aspect of [topic] you'd like information about?"

Generate only the clarification request, no additional commentary."""

PREDICTION_DECISION_PROMPT = """Analyze the user's message and current state to determine what action is needed.

CURRENT STATE CONTEXT:
- Current Patient ID: {current_patient_id}
- Has Maternal Report: {has_maternal_report}
- Has Fetal Report: {has_fetal_report}
- Has Patient Data: {has_patient_data}
- Has RAG Context: {has_rag_context}

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

CLASSIFICATION RULES:

1. REASSESSMENT DETECTION:
   If user explicitly requests reassessment using words like "recheck", "reassess", "again", "test again", "redo", "update assessment":
   - ALWAYS classify as the requested assessment type (maternal/fetal/both) even if reports already exist
   - This forces a new assessment to be run

2. NEW PATIENT DETECTION:
   If a different patient ID/name is mentioned than the current patient:
   - Clear context and assess as new patient

3. ASSESSMENT CATEGORIES:
   - "maternal": Maternal health RISK ASSESSMENT needed (gestational diabetes, pregnancy complications)
     * Only classify if: maternal_report doesn't exist OR reassessment explicitly requested
   
   - "fetal": Fetal health RISK ASSESSMENT needed (baby's health prediction)
     * Only classify if: fetal_report doesn't exist OR reassessment explicitly requested
   
   - "both": Both maternal AND fetal assessments needed
     * Only classify if: neither report exists OR reassessment explicitly requested
     * If one report exists and user asks for both, classify as the missing one

4. KNOWLEDGE QUERY:
   - "rag": Medical/clinical QUESTIONS requiring literature retrieval:
     * Medication safety and contraindications
     * Clinical guidelines and best practices
     * Treatment protocols and procedures
     * Nutritional and lifestyle recommendations
     * Symptom explanations and medical definitions
     * General antenatal care knowledge questions

5. FOLLOWUP/CLARIFICATION:
   - "respond": User is asking about existing data, following up, or casual conversation:
     * Questions about existing patient data (e.g., "what was the HDL value?")
     * Clarification requests (e.g., "explain further", "what does that mean?")
     * Greetings, thanks, small talk
     * References to previous responses

IMPORTANT DISTINCTIONS:
- "assess patient X for GD" → maternal (if no report) or respond (if report exists, unless reassessment requested)
- "what are symptoms of GD?" → rag
- "what was patient X's BMI?" → respond (data inquiry)
- "explain the risk score" → respond (followup on existing report)
- "recheck patient X" → maternal/fetal/both (reassessment)

Respond with ONLY one word: maternal, fetal, both, rag, or respond"""

PATIENT_ID_EXTRACTION_PROMPT = """Extract the patient identifier (name or ID) from the user's message.

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

CURRENT PATIENT ID IN SYSTEM: {current_patient_id}

Instructions:
- Look for patient ID or name in the current message
- If not found in current message but exists in conversation history or system, return the existing one
- If multiple are mentioned, return the first one
- If none found anywhere, return "NONE"

Return ONLY the patient identifier (name or ID)."""

GGENERATE_KEYWORDS_PROMPT = """Generate simple, direct search keywords/phrases for finding medical management information.

USER QUESTION:
{user_message}

MATERNAL HEALTH REPORT:
{maternal_report}

FETAL HEALTH REPORT:
{fetal_report}

INSTRUCTION:
Look at the health reports and user question. Identify the main health issues mentioned. For each issue, create simple keywords about how to manage it during pregnancy.

GENERATE KEYWORDS LIKE (BASED ON THE REPORTS) EXAMPLES:
- "management for gestational diabetes"
- "lowering blood pressure in pregnancy" 
- "treating anemia in pregnant women"
- "managing morning sickness"
- "fetal growth monitoring"

RULES:
1. Keep it SIMPLE and DIRECT
2. Focus on MANAGEMENT/TREATMENT
3. Make 5-8 phrases.


EXAMPLES:
If report shows: gestational diabetes, hypertension
Good keywords: "managing diabetes in pregnancy, lowering blood pressure when pregnant, diet for gestational diabetes, safe blood pressure medication pregnancy"

If report shows: anemia, nausea
Good keywords: "treating anemia in pregnancy, managing morning sickness, iron supplements for pregnant women, reducing nausea during pregnancy"

If report shows: fetal growth issues
Good keywords: "managing fetal growth restriction, monitoring baby growth in womb, when to deliver small baby"

Generate keywords:"""

SHOULD_RETRIEVE_PROMPT = """Determine if patient data needs to be loaded for the current user request.

USER QUESTION:
{user_message}

CONVERSATION HISTORY:
{conversation_history}

CURRENT STATE:
- Current Patient ID in State: {current_patient_id}
- Has Patient Data: {has_patient_data}

Patient Data Summary (if available):
{patient_data_summary}

EXTRACTION RULES:
1. Extract patient identifier from the message:
   - Patient IDs: P001, P002, P003, etc.
   - Patient names: Sarah, Mrs. Johnson, etc.
   - Pronouns: "she", "he", "the patient", "her", "him" (check history for reference)
   - Implicit references: "check the patient", "assess", "update" (if patient context exists)

2. If NO patient identifier can be found → not_load

DECISION LOGIC:

LOAD PATIENT DATA if:
- User mentions a SPECIFIC patient ID (P001, P004, etc.) AND that patient is NOT the current patient in state
- User mentions a patient name AND no matching patient data exists
- User asks for patient-specific information (name, age, test results, history)
- User requests an ASSESSMENT of a specific patient
- Current patient context exists but patient data is NOT loaded

DO NOT LOAD if:
- NO patient identifier is mentioned in the message
- The mentioned patient is ALREADY the current patient in state AND data is loaded
- General medical questions without patient reference
- Greetings, thanks, or procedural messages
- Question can be answered from existing conversation history without new data

EXAMPLES:
- "What is patient P004's name?" → load (needs P004's data)
- "How is Sarah doing?" → load (needs Sarah's data)
- "Update on P001" (and P001 is NOT current patient) → load
- "Assess P002" → load
- "What were her latest test results?" (if "her" refers to current patient with data) → not_load
- "What is preeclampsia?" → not_load (no patient reference)
- "Hello" → not_load

SPECIAL CASES:
- If user says "same patient" or continues conversation about current patient → not_load
- Brief references like "check her" when current patient exists → not_load
- "Switch to P003" or "What about P002?" → load

ANALYSIS STEPS:
1. Extract patient identifier from message
2. Check if identifier matches current patient in state
3. Check if patient data is already loaded for that identifier
4. Decide: load (needs new data) or not_load (data exists or not needed)

Respond with ONLY: load or not_load"""

RAG_RESPONSE_PROMPT = """Provide a medically accurate response based ONLY on the available context. Do not use any external knowledge.

RETRIEVED MEDICAL CONTEXT:
{rag_context}

ADDITIONAL CONTEXT (if relevant):
Maternal Report: {maternal_report}
Fetal Report: {fetal_report}

USER QUESTION:
{user_question}

STRICT RESPONSE RULES:
1. **STRICT CONTEXT-ONLY POLICY**: Use ONLY information from the provided context above
2. **NO EXTRAPOLATION**: Do not infer, assume, or add information not explicitly in context
3. **ACCURACY MANDATE**: If information is not in context, state this clearly
4. **NO GENERALIZATION**: Do not provide general medical advice not supported by context
5. **CITATION REQUIREMENT**: Reference specific information from context when possible

RESPONSE STRUCTURE:
1. **Direct Answer**: Based strictly on retrieved context
2. **Limitations**: Clearly state if information is incomplete or missing
3. **No Speculation**: Do not fill gaps with general knowledge

SPECIAL CASES:
- If user asks about a topic NOT covered in context → "The available medical literature does not contain specific information about [topic]. Please consult clinical guidelines or a healthcare provider."
- If context is incomplete for the question → "Based on the available information, [partial answer]. However, complete information on [missing aspect] is not provided in the retrieved context."
- If no relevant context at all → "No specific medical information is available in the retrieved context to address this question. Please refer to current clinical guidelines."

MEDICAL PRECAUTIONS:
- Always emphasize that this is informational support only
- Recommend consultation with healthcare providers
- Note that medical management requires individual assessment

Generate response:"""

PREDICTION_DECISION_PROMPT = """Analyze the user's message and current state to determine what action is needed.

CURRENT STATE CONTEXT:
- Current Patient ID: {current_patient_id}
- Has Maternal Report: {has_maternal_report}
- Has Fetal Report: {has_fetal_report}
- Has Patient Data: {has_patient_data}
- Has RAG Context: {has_rag_context}

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

CLASSIFICATION RULES:

1. REASSESSMENT DETECTION:
   If user explicitly requests reassessment using words like "recheck", "reassess", "again", "test again", "redo", "update assessment":
   - ALWAYS classify as the requested assessment type (maternal/fetal/both) even if reports already exist
   - This forces a new assessment to be run

2. NEW PATIENT DETECTION:
   If a different patient ID/name is mentioned than the current patient:
   - Clear context and assess as new patient

3. ASSESSMENT CATEGORIES:
   - "maternal": Maternal health RISK ASSESSMENT needed (gestational diabetes, pregnancy complications)
     * ONLY classify as maternal if user asks for ASSESSMENT/TEST/CHECK of MATERNAL health
     * Examples: "assess P001 for gestational diabetes", "test for anemia", "check maternal health"
     * NOT: "what is gestational diabetes?" (that's rag)
   
   - "fetal": Fetal health RISK ASSESSMENT needed (baby's health prediction)
     * ONLY classify as fetal if user asks for ASSESSMENT/TEST/CHECK of FETAL health
     * Examples: "assess fetal health", "check baby's wellbeing"
   
   - "both": Both maternal AND fetal assessments needed
     * Only if user explicitly requests both assessments
     * Examples: "full assessment", "complete checkup"

4. KNOWLEDGE QUERY:
   - "rag": Medical/clinical QUESTIONS requiring literature retrieval:
     * Medical information questions (what, how, when, why)
     * "what is gestational diabetes?" → rag
     * "how is anemia treated in pregnancy?" → rag  
     * "symptoms of preeclampsia" → rag
     * "medications safe during pregnancy" → rag
     * "clinical guidelines for GD management" → rag
     * BUT: If existing RAG context already answers this question → respond

5. FOLLOWUP/CLARIFICATION:
   - "respond": User is asking about existing data, following up, or casual conversation:
     * Questions about existing patient data/reports
     * Follow-up questions on previous assessments
     * Clarification requests
     * Greetings, thanks, small talk
     * Medical questions already answered in existing RAG context

6. RAG CONTEXT CHECK:
   - Before classifying as "rag", check if question can be answered from existing RAG context
   - If user asks about a topic already covered in existing RAG context → respond
   - Only use "rag" if question requires NEW medical literature retrieval

DECISION FLOWCHART:
1. Does user request REASSESSMENT? → maternal/fetal/both
2. Does user request NEW PATIENT assessment? → maternal/fetal/both
3. Is this a MEDICAL KNOWLEDGE question?
   - Yes: Check if existing RAG context answers it
     - If yes → respond
     - If no → rag
4. Is this a PATIENT ASSESSMENT request?
   - Maternal assessment request → maternal
   - Fetal assessment request → fetal  
   - Both assessment request → both
5. Otherwise → respond

SPECIFIC EXAMPLES:
- "what is gestational diabetes?" → rag (medical knowledge)
- "assess P001 for gestational diabetes" → maternal (assessment request)
- "what are the symptoms of anemia?" → rag (medical knowledge)  
- "check patient for anemia" → maternal (assessment request)
- "explain my last report" → respond (follow-up on existing)
- "hello" → respond (casual)
- "what was the blood pressure reading?" → respond (data inquiry)
- "how to manage hypertension in pregnancy?" → rag (medical knowledge)

Respond with ONLY one word: maternal, fetal, both, rag, or respond"""

RESPOND_PROMPT = """Generate an appropriate response based on the available context.

AVAILABLE CONTEXT:
{context_summary}

USER MESSAGE:
{user_message}

CONVERSATION HISTORY:
{conversation_history}

Instructions:
- Determine what type of response is needed based on the user's message
- Do NOT invent or assume information. Only asnwer based on the provided context and information. 
- If the message requires medical or medication guidance that cannot be safely answered with the given context, respond with: "There is not enough information in the available context to answer this safely."
- Decide the legth of the response based on the CONTEXT and USER MESSAGE, polite talk and out-of-scope requests should be short and concise.
- Give follow up suggestions based on the user input or system prompt only if it makes sense to do so.
- If asking about patient data, provide the specific information
- If asking for clarification, explain clearly
- If casual conversation, respond appropriately
- Be helpful, professional, and concise"""