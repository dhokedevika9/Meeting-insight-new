import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd
from utils.database import get_all_meetings
import numpy as np

def knowledge_graph_component():
    """Component for displaying knowledge graph visualization."""
    
    st.header("🕸️ Knowledge Graph")
    st.markdown("Explore connections between topics, decisions, and action items across all meetings.")
    
    # Get all meetings
    meetings = get_all_meetings()
    
    if not meetings:
        st.info("📭 No meetings processed yet. Upload meetings to generate knowledge graphs!")
        return
    
    # Filter meetings with knowledge graph data
    meetings_with_kg = [m for m in meetings if m.get('knowledge_graph')]
    
    if not meetings_with_kg:
        st.info("🔄 No knowledge graph data available. This feature requires processed meetings with AI analysis.")
        return
    
    # Graph type selection
    st.subheader("🎛️ Graph Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        graph_type = st.selectbox(
            "Graph Type",
            ["Combined Graph", "Individual Meeting", "Topic Connections", "Action Item Network"]
        )
    
    with col2:
        # Meeting selection for individual graphs
        if graph_type == "Individual Meeting":
            meeting_options = [f"{m['filename']} ({m['upload_date']})" for m in meetings_with_kg]
            selected_meeting_idx = st.selectbox(
                "Select Meeting",
                range(len(meeting_options)),
                format_func=lambda x: meeting_options[x]
            )
            selected_meeting = meetings_with_kg[selected_meeting_idx]
        else:
            selected_meeting = None
    
    with col3:
        layout_type = st.selectbox(
            "Layout Algorithm",
            ["Force-directed", "Circular", "Hierarchical", "Random"]
        )
    
    # Generate and display graph
    if graph_type == "Combined Graph":
        display_combined_knowledge_graph(meetings_with_kg, layout_type)
    elif graph_type == "Individual Meeting" and selected_meeting:
        display_individual_meeting_graph(selected_meeting, layout_type)
    elif graph_type == "Topic Connections":
        display_topic_connections_graph(meetings_with_kg, layout_type)
    elif graph_type == "Action Item Network":
        display_action_item_network(meetings_with_kg, layout_type)

def display_combined_knowledge_graph(meetings, layout_type):
    """Display a combined knowledge graph from all meetings."""
    
    st.subheader("🌐 Combined Knowledge Graph")
    
    # Combine all knowledge graphs
    all_nodes = []
    all_edges = []
    
    for meeting in meetings:
        kg = meeting.get('knowledge_graph', {})
        meeting_id = meeting['id']
        meeting_name = meeting['filename'][:20]
        
        # Add meeting node
        meeting_node = {
            'id': f"meeting_{meeting_id}",
            'label': f"📁 {meeting_name}",
            'type': 'meeting',
            'weight': 10,
            'meeting_id': meeting_id
        }
        all_nodes.append(meeting_node)
        
        # Add nodes from knowledge graph
        for node in kg.get('nodes', []):
            node_copy = node.copy()
            node_copy['id'] = f"meeting_{meeting_id}_{node['id']}"
            node_copy['meeting_id'] = meeting_id
            all_nodes.append(node_copy)
        
        # Add edges from knowledge graph
        for edge in kg.get('edges', []):
            edge_copy = edge.copy()
            edge_copy['source'] = f"meeting_{meeting_id}_{edge['source']}"
            edge_copy['target'] = f"meeting_{meeting_id}_{edge['target']}"
            edge_copy['meeting_id'] = meeting_id
            all_edges.append(edge_copy)
        
        # Connect meeting node to its content
        for node in kg.get('nodes', []):
            meeting_edge = {
                'source': f"meeting_{meeting_id}",
                'target': f"meeting_{meeting_id}_{node['id']}",
                'relationship': 'contains',
                'weight': 5,
                'meeting_id': meeting_id
            }
            all_edges.append(meeting_edge)
    
    # Create and display graph
    if all_nodes and all_edges:
        fig = create_network_graph(all_nodes, all_edges, layout_type, "Combined Knowledge Graph")
        st.plotly_chart(fig, use_container_width=True)
        
        # Display graph statistics
        display_graph_statistics(all_nodes, all_edges)
    else:
        st.warning("No graph data available to display.")

def display_individual_meeting_graph(meeting, layout_type):
    """Display knowledge graph for a single meeting."""
    
    st.subheader(f"📊 Knowledge Graph: {meeting['filename']}")
    
    kg = meeting.get('knowledge_graph', {})
    nodes = kg.get('nodes', [])
    edges = kg.get('edges', [])
    
    if nodes and edges:
        fig = create_network_graph(nodes, edges, layout_type, f"Knowledge Graph: {meeting['filename']}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Display detailed node and edge information
        display_meeting_graph_details(nodes, edges)
    else:
        st.warning("No knowledge graph data available for this meeting.")

def display_topic_connections_graph(meetings, layout_type):
    """Display a graph showing topic connections across meetings."""
    
    st.subheader("🏷️ Topic Connections Across Meetings")
    
    # Extract topics and their connections
    topic_nodes = []
    topic_edges = []
    topic_connections = {}
    
    for meeting in meetings:
        topics = meeting.get('topics', [])
        meeting_name = meeting['filename'][:20]
        
        for topic in topics:
            topic_keywords = topic.get('keywords', [])
            if topic_keywords:
                topic_label = ', '.join(topic_keywords[:3])
                topic_id = f"topic_{topic_label.replace(', ', '_').replace(' ', '_')}"
                
                # Add topic node
                if topic_id not in topic_connections:
                    topic_connections[topic_id] = {
                        'meetings': [],
                        'weight': 0
                    }
                
                topic_connections[topic_id]['meetings'].append(meeting_name)
                topic_connections[topic_id]['weight'] += topic.get('weight', 1)
    
    # Create nodes for topics
    for topic_id, data in topic_connections.items():
        topic_label = topic_id.replace('topic_', '').replace('_', ' ')
        topic_nodes.append({
            'id': topic_id,
            'label': f"🏷️ {topic_label}",
            'type': 'topic',
            'weight': min(data['weight'] * 10, 15),
            'meetings': data['meetings']
        })
    
    # Create edges between topics that appear in the same meetings
    for i, node1 in enumerate(topic_nodes):
        for j, node2 in enumerate(topic_nodes[i+1:], i+1):
            common_meetings = set(node1['meetings']) & set(node2['meetings'])
            if common_meetings:
                topic_edges.append({
                    'source': node1['id'],
                    'target': node2['id'],
                    'relationship': 'co_occurs',
                    'weight': len(common_meetings) * 2,
                    'common_meetings': list(common_meetings)
                })
    
    if topic_nodes:
        fig = create_network_graph(topic_nodes, topic_edges, layout_type, "Topic Connections")
        st.plotly_chart(fig, use_container_width=True)
        
        # Display topic statistics
        st.markdown("#### 📊 Topic Statistics")
        topic_df = pd.DataFrame([
            {
                'Topic': node['label'].replace('🏷️ ', ''),
                'Meetings': len(node['meetings']),
                'Weight': f"{node['weight']:.2f}"
            }
            for node in topic_nodes
        ])
        st.dataframe(topic_df, use_container_width=True)
    else:
        st.warning("No topic connections found.")

def display_action_item_network(meetings, layout_type):
    """Display a network of action items and responsible parties."""
    
    st.subheader("📋 Action Item Network")
    
    action_nodes = []
    action_edges = []
    people = set()
    
    for meeting in meetings:
        summary = meeting.get('summary', {})
        action_items = summary.get('action_items', [])
        meeting_name = meeting['filename'][:20]
        
        for i, item in enumerate(action_items):
            if isinstance(item, dict):
                action_text = item.get('item', '')
                responsible_party = item.get('responsible_party', 'Unassigned')
            else:
                action_text = str(item)
                responsible_party = 'Unassigned'
            
            # Create action item node
            action_id = f"action_{meeting['id']}_{i}"
            action_nodes.append({
                'id': action_id,
                'label': f"📋 {action_text[:30]}...",
                'type': 'action_item',
                'weight': 8,
                'meeting': meeting_name,
                'full_text': action_text
            })
            
            # Add person if not unassigned
            if responsible_party != 'Unassigned':
                people.add(responsible_party)
                
                # Create edge to responsible party
                action_edges.append({
                    'source': action_id,
                    'target': f"person_{responsible_party}",
                    'relationship': 'assigned_to',
                    'weight': 5
                })
    
    # Add person nodes
    for person in people:
        action_nodes.append({
            'id': f"person_{person}",
            'label': f"👤 {person}",
            'type': 'person',
            'weight': 12
        })
    
    if action_nodes:
        fig = create_network_graph(action_nodes, action_edges, layout_type, "Action Item Network")
        st.plotly_chart(fig, use_container_width=True)
        
        # Display action item statistics
        st.markdown("#### 📊 Action Item Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_actions = len([n for n in action_nodes if n['type'] == 'action_item'])
            st.metric("Total Action Items", total_actions)
        
        with col2:
            total_people = len([n for n in action_nodes if n['type'] == 'person'])
            st.metric("People Involved", total_people)
        
        with col3:
            assigned_actions = len([e for e in action_edges if e['relationship'] == 'assigned_to'])
            st.metric("Assigned Actions", assigned_actions)
    else:
        st.warning("No action items found.")

def create_network_graph(nodes, edges, layout_type, title):
    """Create a network graph using Plotly."""
    
    # Create NetworkX graph for layout calculation
    G = nx.Graph()
    
    # Add nodes
    for node in nodes:
        G.add_node(node['id'], **node)
    
    # Add edges
    for edge in edges:
        weight = edge.get('weight', 1)
        G.add_edge(edge['source'], edge['target'], weight=weight, **edge)
    
    # Calculate layout
    if layout_type == "Force-directed":
        pos = nx.spring_layout(G, k=3, iterations=50)
    elif layout_type == "Circular":
        pos = nx.circular_layout(G)
    elif layout_type == "Hierarchical":
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            pos = nx.spring_layout(G)
    else:  # Random
        pos = nx.random_layout(G)
    
    # Prepare data for Plotly
    edge_x = []
    edge_y = []
    edge_info = []
    
    for edge in edges:
        x0, y0 = pos[edge['source']]
        x1, y1 = pos[edge['target']]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_info.append(f"{edge['source']} → {edge['target']}<br>Relationship: {edge.get('relationship', 'N/A')}")
    
    # Create edge trace
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Prepare node data
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_info = []
    
    # Color mapping for node types
    color_map = {
        'topic': '#FF6B6B',
        'decision': '#4ECDC4',
        'action': '#45B7D1',
        'person': '#96CEB4',
        'meeting': '#FFEAA7',
        'action_item': '#DDA0DD'
    }
    
    for node in nodes:
        x, y = pos[node['id']]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node['label'])
        node_color.append(color_map.get(node['type'], '#888'))
        node_size.append(max(node.get('weight', 5), 5))
        
        # Create hover info
        info = f"<b>{node['label']}</b><br>"
        info += f"Type: {node['type']}<br>"
        if 'meetings' in node:
            info += f"Meetings: {', '.join(node['meetings'])}<br>"
        if 'full_text' in node:
            info += f"Full text: {node['full_text']}<br>"
        node_info.append(info)
    
    # Create node trace
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_info,
        text=node_text,
        textposition="middle center",
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color='white')
        )
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=title,
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Hover over nodes for details",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=600
                    ))
    
    return fig

def display_graph_statistics(nodes, edges):
    """Display statistics about the knowledge graph."""
    
    st.subheader("📊 Graph Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Nodes", len(nodes))
    
    with col2:
        st.metric("Total Edges", len(edges))
    
    with col3:
        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        most_common_type = max(node_types.items(), key=lambda x: x[1])[0] if node_types else "N/A"
        st.metric("Most Common Type", most_common_type)
    
    with col4:
        # Calculate average connections
        if nodes:
            avg_connections = (len(edges) * 2) / len(nodes)  # Each edge connects 2 nodes
            st.metric("Avg Connections", f"{avg_connections:.1f}")
        else:
            st.metric("Avg Connections", "0")
    
    # Node type distribution
    if node_types:
        st.markdown("#### 🏷️ Node Type Distribution")
        type_df = pd.DataFrame(list(node_types.items()), columns=['Type', 'Count'])
        
        fig = px.pie(type_df, values='Count', names='Type', title='Node Types')
        st.plotly_chart(fig, use_container_width=True)

def display_meeting_graph_details(nodes, edges):
    """Display detailed information about nodes and edges in a meeting graph."""
    
    st.subheader("📋 Graph Details")
    
    tab1, tab2 = st.tabs(["🔘 Nodes", "🔗 Edges"])
    
    with tab1:
        st.markdown("#### Node Details")
        
        node_data = []
        for node in nodes:
            node_data.append({
                'ID': node.get('id', 'N/A'),
                'Label': node.get('label', 'N/A'),
                'Type': node.get('type', 'N/A'),
                'Weight': node.get('weight', 'N/A')
            })
        
        if node_data:
            node_df = pd.DataFrame(node_data)
            st.dataframe(node_df, use_container_width=True)
    
    with tab2:
        st.markdown("#### Edge Details")
        
        edge_data = []
        for edge in edges:
            edge_data.append({
                'Source': edge.get('source', 'N/A'),
                'Target': edge.get('target', 'N/A'),
                'Relationship': edge.get('relationship', 'N/A'),
                'Weight': edge.get('weight', 'N/A')
            })
        
        if edge_data:
            edge_df = pd.DataFrame(edge_data)
            st.dataframe(edge_df, use_container_width=True)
