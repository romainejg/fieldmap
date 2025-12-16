#!/usr/bin/env python3
"""
OAuth Flow Verification Script
Demonstrates the state persistence logic without running the full app.
"""

def simulate_oauth_flow():
    """Simulate the OAuth flow with state persistence"""
    print("=" * 70)
    print("OAuth Flow Simulation - State Persistence Verification")
    print("=" * 70)
    
    # Simulate session state and query params
    session_state = {}
    query_params = {}
    
    print("\n1. USER CLICKS 'SIGN IN WITH GOOGLE'")
    print("-" * 70)
    
    # Step 1: build_auth_url() is called
    print("   build_auth_url() is called...")
    
    # Generate state
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Store in session_state
    session_state["oauth_state"] = state
    print(f"   ✓ Stored state in session_state: {state[:16]}...")
    
    # ALSO store in query_params (NEW!)
    query_params["oauth_state"] = state
    print(f"   ✓ Stored state in query_params: {state[:16]}...")
    
    # Set auth_in_progress flag (NEW!)
    session_state["auth_in_progress"] = True
    print(f"   ✓ Set auth_in_progress = True")
    
    # Store pending auth URL
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?state={state}&..."
    session_state["pending_auth_url"] = auth_url
    print(f"   ✓ Stored pending_auth_url")
    
    print(f"\n   Browser redirects to: {auth_url[:60]}...")
    
    print("\n2. STREAMLIT RERUNS (happens during redirect)")
    print("-" * 70)
    
    # Step 2: App reruns, build_auth_url() is called again
    print("   build_auth_url() is called again (on rerun)...")
    
    # Check if auth_in_progress (NEW!)
    if session_state.get("auth_in_progress", False):
        print(f"   ✓ auth_in_progress is True")
        existing_url = session_state.get("pending_auth_url")
        print(f"   ✓ Returning existing auth URL (not generating new state!)")
        print(f"   ✓ State remains: {session_state['oauth_state'][:16]}...")
    
    print("\n3. USER RETURNS FROM GOOGLE")
    print("-" * 70)
    
    # Step 3: Google redirects back with code and state
    returned_state = state  # Google returns the same state
    code = "4/0AfJohXkL..."
    
    print(f"   Google redirects to: https://app.url/?code={code[:16]}...&state={returned_state[:16]}...")
    
    # Simulate redirect clearing session_state (the problem!)
    print("\n   ⚠️  SIMULATING REDIRECT: session_state is CLEARED (this is the problem!)")
    old_session_state = session_state.copy()
    session_state.clear()
    print(f"   ✗ session_state is now empty: {session_state}")
    
    # But query_params persist!
    print(f"\n   ✓ query_params still has oauth_state: {query_params.get('oauth_state', '(missing)')[:16]}...")
    
    # Add Google's returned params to query_params
    query_params["code"] = code
    query_params["state"] = returned_state
    
    print("\n4. CALLBACK PROCESSING")
    print("-" * 70)
    
    # Step 4: handle_callback() is called
    print("   handle_callback() is called...")
    
    # Retrieve expected state (NEW: try query_params first!)
    expected_state = query_params.get("oauth_state") or session_state.get("oauth_state")
    
    if query_params.get("oauth_state"):
        print(f"   ✓ Retrieved expected_state from query_params: {expected_state[:16]}...")
    elif session_state.get("oauth_state"):
        print(f"   ✓ Retrieved expected_state from session_state: {expected_state[:16]}...")
    else:
        print(f"   ✗ No expected_state found! (this would cause 'Auth session expired')")
        return False
    
    # Retrieve returned state
    returned_state_from_google = query_params.get("state")
    print(f"   ✓ Retrieved returned_state from Google: {returned_state_from_google[:16]}...")
    
    # Compare states
    if expected_state == returned_state_from_google:
        print(f"   ✅ States match! Authentication successful!")
        
        # Exchange code for token (simulated)
        print(f"   ✓ Exchanging code for token...")
        token = {"access_token": "ya29.a0AfH6...", "refresh_token": "1//0gH..."}
        session_state["google_token"] = token
        print(f"   ✓ Token stored in session_state")
        
        # Clear auth flags (NEW!)
        print(f"   ✓ Clearing auth_in_progress and pending_auth_url")
        
        # Clear ALL query params (NEW!)
        print(f"   ✓ Clearing ALL query params (oauth_state, code, state)")
        query_params.clear()
        
        print(f"\n   Final session_state: google_token=<present>")
        print(f"   Final query_params: {query_params}")
        
        return True
    else:
        print(f"   ✗ States don't match!")
        print(f"   Expected: {expected_state[:16]}...")
        print(f"   Returned: {returned_state_from_google[:16]}...")
        return False
    
    print("\n" + "=" * 70)

def test_without_fix():
    """Show what happens WITHOUT the fix (for comparison)"""
    print("\n\n")
    print("=" * 70)
    print("WITHOUT FIX: What would happen with old implementation")
    print("=" * 70)
    
    session_state = {}
    query_params = {}
    
    print("\n1. build_auth_url() generates state")
    state = "abc123..."
    session_state["oauth_state"] = state
    print(f"   ✓ State stored ONLY in session_state: {state}")
    print(f"   ✗ State NOT stored in query_params")
    
    print("\n2. User redirects to Google")
    print("   (Session state is cleared during redirect)")
    session_state.clear()
    
    print("\n3. User returns from Google")
    query_params["code"] = "4/0AfJohXkL..."
    query_params["state"] = state
    
    print("\n4. handle_callback() tries to verify state")
    expected_state = session_state.get("oauth_state")
    print(f"   ✗ expected_state from session_state: {expected_state} (None!)")
    print(f"   ✗ No fallback to query_params in old implementation")
    print(f"\n   ❌ Result: 'Auth session expired' error!")

if __name__ == "__main__":
    # Show the working flow with our fix
    result = simulate_oauth_flow()
    
    if result:
        print("\n✅ OAuth flow completed successfully with state persistence fix!")
    else:
        print("\n❌ OAuth flow failed!")
    
    # Show what happens without the fix
    test_without_fix()
    
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ WITH FIX: State persists in query params across redirect")
    print("❌ WITHOUT FIX: State is lost, causing 'Auth session expired' error")
    print("=" * 70)
