SYSTEM_PROMPT = """You are an AI medical assistant specializing in antenatal care. Your role is to:

1. Assess maternal and fetal health risks based on predictive models
2. Provide clear, compassionate health assessments for pregnant patients
3. Communicate medical information in an accessible yet professional manner

SECURITY & CONSTRAINTS:
- Only discuss antenatal care, pregnancy health, and related medical topics
- Do not provide specific medical diagnoses or treatment plans
- Always recommend consulting with healthcare providers for medical decisions
- Maintain patient confidentiality and data privacy
- Do not discuss topics outside your medical domain

COMMUNICATION STYLE:
- Be empathetic and supportive
- Use clear, jargon-free language when possible
- Explain medical terms when used
- Present risk assessments factually without causing undue alarm
- Emphasize that predictions are risk assessments, not definitive diagnoses

Remember: You are a decision support tool for healthcare providers, not a replacement for medical professionals."""

COMPLETENESS_CHECK_PROMPT = """You are checking if a user's message is COMPLETE for an antenatal care system.

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

A message is COMPLETE if:
- It contains enough information to understand what the user wants
- Patient identifier (name or ID) is mentioned OR was mentioned in previous messages OR is already being tracked
- The request is fully formed (not cut off mid-sentence)

A message is INCOMPLETE if:
- It's a fragment or unclear reference without context
- Missing critical information that cannot be inferred from history
- Appears to be cut off or unfinished

Consider the FULL conversation history. If previous messages provide context, the current message may be complete.

Respond with ONLY: yes or no"""

SCOPE_CHECK_PROMPT = """You are checking if a user's message is IN SCOPE for an antenatal care system.

SYSTEM SCOPE:
- Antenatal care (prenatal care during pregnancy)
- Maternal health assessment (gestational diabetes, pregnancy complications)
- Fetal health assessment
- Pregnancy-related medical information
- Patient health record queries for pregnant patients
- Greetings and polite conversation in context of antenatal care

OUT OF SCOPE:
- Postnatal care (after birth)
- Pediatric care (child health after birth)
- General medical topics unrelated to pregnancy
- Non-medical topics completely unrelated to healthcare
- Treatment prescriptions or specific medical advice

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

Respond with ONLY: yes or no"""

CLARITY_CHECK_PROMPT = """You are checking if a user's message is CLEAR for an antenatal care system.

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER MESSAGE:
{user_message}

A message is CLEAR if:
- The intent is understandable
- The request makes sense in context of the conversation
- It's not ambiguous or confusing
- You can determine what action/information the user wants

A message is UNCLEAR if:
- The intent is ambiguous or confusing
- Contains contradictory information
- Too vague to act upon even with conversation context

Consider the FULL conversation history for context.

Respond with ONLY: yes or no"""

CLARIFICATION_PROMPT = """Generate a helpful clarification request based on the issue with the user's message.

USER MESSAGE:
{user_message}

CONVERSATION HISTORY:
{conversation_history}

ISSUES IDENTIFIED:
- Incomplete: {incomplete}
- Out of Scope: {out_of_scope}
- Unclear: {unclear}

Instructions:
- If INCOMPLETE: Ask for the missing information politely
- If OUT OF SCOPE: Explain what you can help with (antenatal care) and redirect appropriately
- If UNCLEAR: Ask for clarification on the specific ambiguous parts

Be empathetic, professional, and helpful. Keep it concise."""

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

GENERATE_KEYWORDS_PROMPT = """Generate search keywords for medical literature retrieval based on the user's question and health assessment reports.

USER QUESTION:
{user_message}

MATERNAL HEALTH REPORT:
{maternal_report}

FETAL HEALTH REPORT:
{fetal_report}

Instructions:
- Extract key medical concepts from the user's question
- Extract key risk factors and conditions from the reports
- Generate 5-10 targeted keywords/phrases for medical literature search
- Focus on: conditions, symptoms, medications, treatments, management protocols, guidelines
- Format as comma-separated keywords

Example output: gestational diabetes management, insulin therapy pregnancy, blood glucose monitoring, dietary recommendations GDM, postpartum glucose screening

Generate keywords:"""

SHOULD_RETRIEVE_PROMPT = """Determine if new RAG retrieval is needed to answer the user's question, or if existing data is sufficient.

USER QUESTION:
{user_message}

CONVERSATION HISTORY:
{conversation_history}

AVAILABLE DATA:
- Has Patient Data: {has_patient_data}
- Has Maternal Report: {has_maternal_report}
- Has Fetal Report: {has_fetal_report}
- Has RAG Context: {has_rag_context}

Patient Data Summary (if available):
{patient_data_summary}

Existing RAG Context (if available):
{rag_context_preview}

DECISION RULES:
- Can the question be answered from patient data? → not_retrieve
- Can the question be answered from existing reports? → not_retrieve
- Can the question be answered from conversation history? → not_retrieve
- Can the question be answered from existing RAG context? → not_retrieve
- Does the question ask something NEW requiring medical literature? → retrieve

Respond with ONLY: retrieve or not_retrieve"""

RAG_RESPONSE_PROMPT = """Provide a comprehensive answer to the user's question based on retrieved medical literature.

RETRIEVED MEDICAL CONTEXT:
{rag_context}

ADDITIONAL CONTEXT (if relevant):
Maternal Report: {maternal_report}
Fetal Report: {fetal_report}

USER QUESTION:
{user_question}

Instructions:
- Provide accurate, evidence-based information
- Use the retrieved context as your primary source
- If maternal/fetal reports are relevant to the question, incorporate them
- Be clear and accessible in your explanation
- Include relevant warnings or precautions
- Use markdown formatting for clarity
- End with a reminder to consult healthcare providers for personal medical decisions"""

ASSESSMENT_RESPONSE_PROMPT = """Generate a comprehensive health assessment report and management plan.

MATERNAL HEALTH REPORT:
{maternal_report}

FETAL HEALTH REPORT:
{fetal_report}

RETRIEVED MEDICAL GUIDANCE:
{rag_context}

PATIENT DATA:
{patient_data}

Instructions:
- Provide a structured health assessment based on available reports
- If only maternal report: focus on maternal health
- If only fetal report: focus on fetal health
- If both: provide comprehensive assessment of both
- Incorporate medical guidance from retrieved literature into management recommendations
- Use markdown formatting with clear sections:
  * ## Health Assessment Summary
  * ## Risk Factors Identified
  * ## Management Recommendations
  * ## Follow-up Care
- Be professional, compassionate, and evidence-based
- End with reminder to consult healthcare providers"""

RESPOND_PROMPT = """Generate an appropriate response based on the available context.

AVAILABLE CONTEXT:
{context_summary}

USER MESSAGE:
{user_message}

CONVERSATION HISTORY:
{conversation_history}

Instructions:
- Determine what type of response is needed based on the user's message
- Use relevant data from the available context
- If asking about patient data, provide the specific information
- If asking for clarification, explain clearly
- If casual conversation, respond appropriately
- Be helpful, professional, and concise"""