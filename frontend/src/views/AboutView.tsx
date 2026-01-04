
import type { Person } from "../aboutdata";

type AboutViewProps = {
  aboutData: Person[];
};

const AboutView = ({ aboutData }: AboutViewProps) => {
  return (

    

    <div className="px-5 py-5 w-full">
    <div className=" bg-emerald-900/80 space-y-5 w-full max-w-none h-full p-6" >

    
    <div className="bg-white text-center py-20">General information</div>

    <div className="flex flex-row space-x-10 text-center">
      <div className="bg-white w-full py-25 px-10">Player</div>
      <div className="bg-white w-full py-25 px-10">Green Keeper</div>
      <div className="bg-white w-full py-25 px-10">Weather</div>
    </div>

    <div className="flex flex-row space-x-10 text-center">
      <div className="bg-white w-full py-25 px-10">Use case</div>
      <div className="bg-white w-full py-10 px-10">
        <text className="text-2xl">
          Developers
          </text> 
        <div className="flex justify-center  flex-row  items-center">
        
        

        {aboutData.map(personLineUpCB)}</div>
        
        </div>
    </div>

    </div>
    </div>
  )
};



function personLineUpCB(person: Person) {
  return (
    <div className="m-12 max-w-96" key={person.id}>
      <div>
        <div>
          <img
            src={person.imgSource}
            className="mt-4 rounded-full object-cover object-top h-40 w-40 mx-auto bg-white"
          />
          <p className="text-center mt-3 text-l mx-auto text-black">
            {person.name}
          </p>
        </div>

        <div className="bg-white text-black mt-2">
          {/* GitHub */}
          <div className="flex items-center justify-center mt-2">
            <img
              src="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png"
              className="w-5 h-5 mr-2"
              alt="GitHub"
            />
            <a href={person.git} target="_blank" className="underline">
              GitHub
            </a>
          </div>

          {/* LinkedIn */}
          {person.linkedIn && (
            <div className="flex items-center justify-center mt-1">
              <img
                src="https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Bug.svg.original.svg"
                className="w-5 h-5 mr-2"
                alt="LinkedIn"
              />
              <a href={person.linkedIn} target="_blank" className="underline">
                LinkedIn
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


export default AboutView
