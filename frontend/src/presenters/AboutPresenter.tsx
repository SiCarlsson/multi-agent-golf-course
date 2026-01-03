import AboutView from '../views/AboutView.tsx'
import { aboutData } from '../aboutdata.ts'

const AboutPresenter = () => {
  return (
    <AboutView aboutData={aboutData}/>
  )
}

export default AboutPresenter