from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes.check_clarity import check_clarity_node
from .nodes.ask_clarification import ask_clarification_node
from .nodes.prediction_decision import prediction_decision_node
from .nodes.load_data import load_data_node
from .nodes.run_maternal import run_maternal_node
from .nodes.run_fetal import run_fetal_node
from .nodes.generate_keywords import generate_keywords_node
from .nodes.should_retrieve import should_retrieve_node
from .nodes.rag_retrieval import rag_retrieval_node
from .nodes.respond import respond_node
from .nodes.respond import respond_node, persist_node 

def create_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("check_clarity", check_clarity_node)
    workflow.add_node("ask_clarification", ask_clarification_node)
    workflow.add_node("decide_prediction", prediction_decision_node)  
    workflow.add_node("load_data", load_data_node)
    workflow.add_node("run_maternal", run_maternal_node)
    workflow.add_node("run_fetal", run_fetal_node)
    workflow.add_node("generate_keywords", generate_keywords_node)
    workflow.add_node("should_retrieve", should_retrieve_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("respond", respond_node)
    workflow.add_node("persist", persist_node)
    
    # Set entry point
    workflow.set_entry_point("check_clarity")
    
    # Route after clarity check
    def route_after_clarity(state: AgentState):
        if (state.get("incomplete") == "yes" or 
            state.get("clear") == "no" or 
            state.get("inscope") == "no"):
            return "ask_clarification"
        return "decide_prediction"  
    
    workflow.add_conditional_edges(
        "check_clarity",
        route_after_clarity,
        {
            "decide_prediction": "decide_prediction",  
            "ask_clarification": "ask_clarification"
        }
    )
    
    workflow.add_edge("ask_clarification", END)
    
    # Route after prediction decision
    def route_after_prediction(state: AgentState):
        decision = state.get("prediction_decision")
        
        if decision in ["maternal", "fetal", "both"]:
            return "load_data"
        elif decision == "rag":
            return "rag_retrieval"
        else:  # respond
            return "should_retrieve"
    
    workflow.add_conditional_edges(
        "decide_prediction",  
        route_after_prediction,
        {
            "load_data": "load_data",
            "rag_retrieval": "rag_retrieval",
            "should_retrieve": "should_retrieve"
        }
    )
    
    # Route after load_data
    def route_after_load_data(state: AgentState):
        decision = state.get("prediction_decision")
        
        if decision == "maternal":
            return "run_maternal"
        elif decision == "fetal":
            return "run_fetal"
        elif decision == "both":
            return "run_maternal"
        
        return "respond"
    
    workflow.add_conditional_edges(
        "load_data",
        route_after_load_data,
        {
            "run_maternal": "run_maternal",
            "run_fetal": "run_fetal",
            "respond": "respond"
        }
    )
    
    # After maternal - check if need fetal too
    def route_after_maternal(state: AgentState):
        decision = state.get("prediction_decision")
        
        if decision == "both":
            return "run_fetal"
        return "generate_keywords"
    
    workflow.add_conditional_edges(
        "run_maternal",
        route_after_maternal,
        {
            "run_fetal": "run_fetal",
            "generate_keywords": "generate_keywords"
        }
    )
    
    # After fetal - always go to generate_keywords
    workflow.add_edge("run_fetal", "generate_keywords")
    
    # After generate_keywords - go to rag_retrieval
    workflow.add_edge("generate_keywords", "rag_retrieval")
    
    # Route after should_retrieve
    def route_after_should_retrieve(state: AgentState):
        decision = state.get("should_load_patient") 
        if decision == "load":
            return "load_data"  
        return "respond"  

    workflow.add_conditional_edges(
        "should_retrieve",
        route_after_should_retrieve,
        {
        "load_data": "load_data",  
        "respond": "respond"
        }
    )
    
    # After rag_retrieval - always go to respond
    workflow.add_edge("rag_retrieval", "respond")

    workflow.add_edge("respond", "persist")
    
    # After respond - END
    workflow.add_edge("persist", END)
    
    # Compile with memory
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph