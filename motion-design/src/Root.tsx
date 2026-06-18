import { Composition } from "remotion";
import { Smoke } from "./scenes/Smoke";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Smoke"
        component={Smoke}
        durationInFrames={30}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
