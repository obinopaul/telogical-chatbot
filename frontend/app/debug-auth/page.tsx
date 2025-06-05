'use client';

export default function DebugAuth() {
  const checkEnvVars = () => {
    const vars = {
      'GOOGLE_CLIENT_ID': process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || 'Not set',
      'NEXTAUTH_URL': process.env.NEXT_PUBLIC_NEXTAUTH_URL || 'Not set',
    };
    
    console.log('Environment Variables Check:', vars);
    alert(JSON.stringify(vars, null, 2));
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Auth Debug Page</h1>
      
      <div className="space-y-4">
        <button 
          onClick={checkEnvVars}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Check Environment Variables
        </button>
        
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Expected Google OAuth URLs:</h2>
          <ul className="text-sm space-y-1">
            <li><strong>Authorized JavaScript origins:</strong> http://localhost:3000</li>
            <li><strong>Authorized redirect URIs:</strong> http://localhost:3000/api/auth/callback/google</li>
          </ul>
        </div>
        
        <div className="bg-yellow-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Check Browser Console for errors!</h2>
          <p className="text-sm">Open DevTools and look for any JavaScript errors when clicking "Continue with Google"</p>
        </div>
      </div>
    </div>
  );
}