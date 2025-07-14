import React, { useState, useEffect } from 'react'
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  FileText,
  Settings,
  Bell,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Briefcase,
  Upload
} from 'lucide-react'

export default function Dashboard() {
  const [selectedJob, setSelectedJob] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [jobsList, setJobsList] = useState([])
  const [jobDetails, setJobDetails] = useState(null)
  const [budgetStatus, setBudgetStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch initial data
  useEffect(() => {
    fetchDashboardData()
    fetchJobsList()
  }, [])

  // Fetch job-specific details when you select one
  useEffect(() => {
    if (selectedJob) {
      fetchJobDetails(selectedJob.id)
      fetchBudgetStatus(selectedJob.id)
    }
  }, [selectedJob])

  async function fetchDashboardData() {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/dashboard/overview', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const result = await res.json()
      if (result.success) {
        setDashboardData(result.data)
        setAlerts(result.data.alerts || [])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function fetchJobsList() {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/dashboard/jobs', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const result = await res.json()
      if (result.success) setJobsList(result.data)
    } catch (err) {
      console.error(err)
    }
  }

  async function fetchJobDetails(jobId) {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/dashboard/job/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const result = await res.json()
      if (result.success) setJobDetails(result.data)
    } catch (err) {
      console.error(err)
    }
  }

  async function fetchBudgetStatus(jobId) {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/budget/status/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const result = await res.json()
      if (result.success) setBudgetStatus(result.data.budget_status)
    } catch (err) {
      console.error(err)
    }
  }

  async function checkAllBudgets() {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/budget/check-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const result = await res.json()
      if (result.success) {
        alert(result.message)
        fetchDashboardData()
        if (selectedJob) fetchBudgetStatus(selectedJob.id)
      }
    } catch (err) {
      console.error(err)
    }
  }

  async function handleFileUpload(file, type) {
    if (!file) return
    try {
      const token = localStorage.getItem('token')
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`/api/upload/${type}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form
      })
      const result = await res.json()
      if (result.success) {
        alert(`${type.toUpperCase()} uploaded`)
        fetchDashboardData()
        if (selectedJob) fetchJobDetails(selectedJob.id)
      } else {
        alert(result.detail || 'Upload error')
      }
    } catch (err) {
      console.error(err)
    }
  }

  async function resolveAlert(alertId) {
    try {
      const token = localStorage.getItem('token')
      await fetch(`/api/alerts/${alertId}/resolve`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchDashboardData()
    } catch (err) {
      console.error(err)
    }
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP'
    }).format(amount)
  }

  function getAlertIcon(sev) {
    if (sev === 'high') return <AlertTriangle className="w-5 h-5 text-red-500" />
    if (sev === 'medium') return <Clock className="w-5 h-5 text-yellow-500" />
    return <Bell className="w-5 h-5 text-blue-500" />
  }

  function getBudgetStatusColor(pct) {
    if (pct >= 90) return 'bg-red-500'
    if (pct >= 80) return 'bg-yellow-500'
    if (pct >= 70) return 'bg-orange-500'
    return 'bg-green-500'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* HEADER */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">NDA Dashboard</h1>
            <p className="text-gray-600">Commercial QS Management System</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={checkAllBudgets}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
            >
              <Settings className="w-4 h-4 mr-1" />
              Check Budgets
            </button>
            <div className="relative">
              <Bell className="w-6 h-6 text-gray-600" />
              {alerts.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {alerts.length}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* NAV TABS */}
        <nav className="mb-8 border-b border-gray-200">
          <ul className="flex space-x-8">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'jobs', label: 'Jobs', icon: Briefcase },
              { id: 'budgets', label: 'Budgets', icon: DollarSign },
              { id: 'alerts', label: 'Alerts', icon: Bell },
              { id: 'files', label: 'Files', icon: Upload }
            ].map(tab => (
              <li key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-2 px-1 border-b-2 text-sm font-medium ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="w-4 h-4 mr-1" />
                  {tab.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* METRIC CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  title: 'Total Contract Value',
                  value: formatCurrency(dashboardData.metrics.total_contract_value),
                  icon: DollarSign,
                  color: 'blue'
                },
                {
                  title: 'Total Invoiced',
                  value: formatCurrency(dashboardData.metrics.total_invoiced),
                  icon: FileText,
                  color: 'green'
                },
                {
                  title: 'Total Costs',
                  value: formatCurrency(dashboardData.metrics.total_costs),
                  icon: TrendingDown,
                  color: 'red'
                },
                {
                  title: 'Active Jobs',
                  value: dashboardData.metrics.active_jobs_count,
                  icon: Briefcase,
                  color: 'purple'
                }
              ].map((card, i) => (
                <div
                  key={i}
                  className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-gray-600">{card.title}</p>
                      <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                    </div>
                    <div className={`p-3 rounded-full bg-${card.color}-100`}>
                      <card.icon className={`w-8 h-8 text-${card.color}-600`} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* SELECT JOB */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium mb-4">Select Job for Details</h3>
              <select
                className="w-full p-3 border rounded-lg"
                value={selectedJob?.id || ''}
                onChange={e => {
                  const job = jobsList.find(j => j.id === +e.target.value)
                  setSelectedJob(job || null)
                }}
              >
                <option value="">-- pick a job --</option>
                {jobsList.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.job_code} – {j.job_name}
                  </option>
                ))}
              </select>
            </div>

            {/* JOB DETAILS */}
            {jobDetails && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* INFO */}
                <section className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-medium mb-4">Job Information</h3>
                  {Object.entries(jobDetails.job_info).map(([k, v]) => (
                    <div key={k} className="flex justify-between mb-2">
                      <span className="text-gray-600">
                        {k.replace(/([A-Z])/g, ' $1')}
                      </span>
                      <span className="font-medium">{v}</span>
                    </div>
                  ))}
                </section>

                {/* FINANCIAL */}
                <section className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-medium mb-4">Financial Summary</h3>
                  {[
                    ['Contract Value', jobDetails.metrics.contract_value],
                    ['Invoiced', jobDetails.metrics.invoiced_amount],
                    ['Total Costs', jobDetails.metrics.total_costs]
                  ].map(([label, amt], i) => (
                    <div key={i} className="flex justify-between mb-2">
                      <span className="text-gray-600">{label}</span>
                      <span className={`font-medium ${
                        label === 'Invoiced' ? 'text-green-600' : label === 'Total Costs' ? 'text-red-600' : ''
                      }`}>
                        {formatCurrency(amt)}
                      </span>
                    </div>
                  ))}
                  <div className="border-t pt-3 flex justify-between">
                    <span className="text-gray-600">Projected Margin</span>
                    <span className={`font-medium ${
                      jobDetails.metrics.projected_margin >= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}>
                      {formatCurrency(jobDetails.metrics.projected_margin)}
                    </span>
                  </div>
                </section>
              </div>
            )}
          </div>
        )}

        {/* JOBS LIST */}
        {activeTab === 'jobs' && (
          <section className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">All Jobs</h3>
            <table className="w-full table-auto">
              <thead>
                <tr className="bg-gray-50">
                  {['Code', 'Name', 'Client', 'Status', 'Progress', 'Value', 'Costs', 'Margin'].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-sm text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dashboardData.jobs_summary.map(job => (
                  <tr key={job.id} className="border-t">
                    <td className="px-3 py-2">{job.job_code}</td>
                    <td className="px-3 py-2">{job.job_name}</td>
                    <td className="px-3 py-2">{job.client}</td>
                    <td className="px-3 py-2 capitalize">{job.status}</td>
                    <td className="px-3 py-2">{job.progress_percentage}%</td>
                    <td className="px-3 py-2">{formatCurrency(job.contract_value)}</td>
                    <td className="px-3 py-2">{formatCurrency(job.total_costs)}</td>
                    <td className="px-3 py-2">{formatCurrency(job.projected_margin)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* BUDGETS */}
        {activeTab === 'budgets' && selectedJob && budgetStatus && (
          <section className="space-y-6">
            <h3 className="text-xl font-medium">Budget Status – {selectedJob.job_code}</h3>
            {Object.entries(budgetStatus).map(([category, data]) => (
              <div key={category} className="bg-white p-4 rounded-lg shadow">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium capitalize">{category}</span>
                  <span className="text-sm">{data.percentage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 h-2 rounded overflow-hidden">
                  <div
                    className={`${getBudgetStatusColor(data.percentage)} h-2`}
                    style={{ width: `${data.percentage}%` }}
                  />
                </div>
                <div className="mt-2 flex justify-between text-sm text-gray-600">
                  <span>Budgeted: {formatCurrency(data.budgeted)}</span>
                  <span>Actual: {formatCurrency(data.actual)}</span>
                </div>
              </div>
            ))}
          </section>
        )}

        {/* ALERTS */}
        {activeTab === 'alerts' && (
          <section className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">Active Alerts</h3>
            {alerts.length === 0 && <p className="text-gray-600">No alerts right now.</p>}
            {alerts.map(a => (
              <div
                key={a.id}
                className="flex justify-between items-center border-t py-3"
              >
                <div className="flex items-center space-x-2">
                  {getAlertIcon(a.severity)}
                  <p>{a.message}</p>
                </div>
                <button
                  onClick={() => resolveAlert(a.id)}
                  className="text-green-600 hover:underline flex items-center"
                >
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Resolve
                </button>
              </div>
            ))}
          </section>
        )}

        {/* FILE UPLOADS */}
        {activeTab === 'files' && (
          <section className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">Upload Reports / CVR</h3>
            <div className="flex space-x-6">
              {[
                { type: 'pnl', label: 'P&L Report' },
                { type: 'invoices', label: 'Invoices Report' },
                { type: 'cvr', label: 'CVR Template' }
              ].map(item => (
                <div key={item.type} className="flex flex-col items-center">
                  <input
                    type="file"
                    id={`file-${item.type}`}
                    className="hidden"
                    onChange={e => handleFileUpload(e.target.files[0], item.type)}
                  />
                  <label
                    htmlFor={`file-${item.type}`}
                    className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {item.label}
                  </label>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}