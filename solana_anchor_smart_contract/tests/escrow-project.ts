import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { EscrowProject } from "../target/types/escrow_project";

describe("escrow-project", () => {
  // Configure the client to use the local cluster.
  anchor.setProvider(anchor.AnchorProvider.env());

  const program = anchor.workspace.EscrowProject as Program<EscrowProject>;

  it("Is initialized!", async () => {
    // Add your test here.
    const tx = await program.methods.initialize().rpc();
    console.log("Your transaction signature", tx);
  });
});
