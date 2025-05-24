import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../config/axios';

interface Lead {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  status: string;
  created_at: string;
}

const LeadsTable: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingLead, setUpdatingLead] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchLeads = async () => {
      try {
        const response = await api.get('/api/v1/leads');
        setLeads(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching leads:', error);
        setError('Failed to fetch leads. Please try again.');
        setLoading(false);
      }
    };

    fetchLeads();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleReachOut = async (leadId: number) => {
    try {
      setUpdatingLead(leadId);
      await api.put(`/api/v1/leads/${leadId}/reached-out`);

      // Update the lead status in the UI
      setLeads(leads.map(lead =>
        lead.id === leadId ? { ...lead, status: 'reached_out' } : lead
      ));

      toast.success('Lead marked as reached out');
    } catch (error) {
      console.error('Error updating lead status:', error);
      toast.error('Failed to update lead status');
    } finally {
      setUpdatingLead(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Leads</h3>
              <p className="mt-1 text-sm text-gray-500">
                  List of all leads in the system
              </p>
          </div>
          <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                      <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Name
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Email
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Date Added
                          </th>
                          <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                          </th>
                      </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                      {leads.length > 0 ? (
                          leads.map((lead) => (
                              <tr key={lead.id} className="hover:bg-gray-50">
                                  <td className="px-6 py-4 whitespace-nowrap">
                                      <div className="text-sm font-medium text-gray-900">
                                          {lead.first_name} {lead.last_name}
                                      </div>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {lead.email}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                          lead.status === 'reached_out'
                                              ? 'bg-green-100 text-green-800'
                                              : 'bg-yellow-100 text-yellow-800'
                                      }`}>
                                          {lead.status.replace('_', ' ')}
                                      </span>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                      {formatDate(lead.created_at)}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                      {lead.status !== 'reached_out' && (
                                          <button
                                              onClick={() => handleReachOut(lead.id)}
                                              disabled={updatingLead === lead.id}
                                              className="text-indigo-600 hover:text-indigo-900 disabled:opacity-50 disabled:cursor-not-allowed"
                                          >
                                              {updatingLead === lead.id ? 'Updating...' : 'Reach Out'}
                                          </button>
                                      )}
                                  </td>
                              </tr>
                          ))
                      ) : (
                          <tr>
                              <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                                  No leads found
                              </td>
                          </tr>
                      )}
                  </tbody>
              </table>
          </div>
      </div>
    </div>
  );
};

export default LeadsTable;
