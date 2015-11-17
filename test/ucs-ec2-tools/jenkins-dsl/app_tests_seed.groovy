import univention.Apps
import univention.Constants
import univention.Jobs

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

// get location (and UCS version) from job name 
def loc = new File(JOB_NAME)
def workdir = loc.getParent()

// better get version from JOB_NAME
println JOB_NAME
println workdir
def version = JOB_NAME.split('/')[0].replace('UCS-', '')
def patch_level = JOB_NAME.split('/')[1].replace('UCS-', '').replace(version, '').replace('-', '')
def last_version = univention.Constants.LAST_VERSION.get(version)

println version
println patch_level

if (last_version == null) {
	throw new RuntimeException("last version for version ${version} not found")
}

def path = workdir + '/Apps'

// create folder, generic app jobs and views
folder(path)
Jobs.createAppStatusViews(this, path)

// get apps from testing, without ucs components
apps = Apps.getApps(version, test=true, ucs_components=false)

//// create jobs for every app
//apps.keySet().sort().each { app ->
//
//  path = workdir + '/Apps/' + app
//
//  // create app folder
//  folder(path)
//  
//  // create  jobs
//  Jobs.createAppAutotestUpdateMultiEnv(this, path, version, patch_level, apps[app])
//  Jobs.createAppAutotestMultiEnv(this, path, version, patch_level, apps[app])
//  Jobs.createAppAutotestMultiEnvUpdateFrom(this, path, version, patch_level, last_version, apps[app])
//
//}
