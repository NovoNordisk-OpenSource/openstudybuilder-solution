export function seedDemoAuth() {
  window.localStorage.setItem(
    'studybuilder.demo.auth.v1',
    JSON.stringify({
      name: 'Smoke Tester',
      roles: [
        'Library.Read',
        'Library.Write',
        'Study.Read',
        'Study.Write',
        'Admin.Read',
        'Admin.Write',
      ],
    })
  )
}
